"""正式媒体上传与查询路由。"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_response, get_current_user, get_db
from app.models.media_file import MediaFile
from app.models.member import Member, UserRole

router = APIRouter()

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_MIME_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
IMAGE_MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
VIDEO_MIME_TO_EXT = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}


def _uploads_dir() -> Path:
    path = Path(__file__).resolve().parents[3] / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


async def _save_upload_file(
    file: UploadFile,
    target: Path,
    max_size: int,
) -> tuple[int, bytes]:
    size = 0
    header = b""
    try:
        with target.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                if not header:
                    header = chunk[:32]
                size += len(chunk)
                if size > max_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="文件大小超过限制",
                    )
                output.write(chunk)
    except Exception:
        if target.exists():
            target.unlink()
        raise
    return size, header


def _validate_magic(content_type: str, header: bytes) -> bool:
    if content_type == "image/jpeg":
        return header.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/gif":
        return header.startswith(b"GIF87a") or header.startswith(b"GIF89a")
    if content_type == "image/webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    if content_type == "video/webm":
        return header.startswith(b"\x1a\x45\xdf\xa3")
    if content_type in {"video/mp4", "video/quicktime"}:
        return len(header) >= 12 and header[4:8] == b"ftyp"
    return False


@router.post("/media/upload-image", response_model=Dict[str, Any])
async def upload_image(
    file: UploadFile = File(...),
    biz_type: str = Form("general"),
    biz_id: int = Form(0),
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    if file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的图片类型")

    ext = IMAGE_MIME_TO_EXT[file.content_type]
    name = f"img_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{hashlib.sha1(os.urandom(16)).hexdigest()[:8]}{ext}"
    target = _uploads_dir() / name
    file_size, header = await _save_upload_file(file, target, MAX_IMAGE_SIZE_BYTES)
    if not _validate_magic(file.content_type, header):
        if target.exists():
            target.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件内容与类型不匹配")

    row = MediaFile(
        biz_type=biz_type,
        biz_id=biz_id,
        file_type="image",
        storage_path=str(target),
        file_name=file.filename or name,
        content_type=file.content_type,
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(
        data={"id": row.id, "file_name": row.file_name, "file_url": f"/uploads/{name}", "file_type": row.file_type},
        message="图片上传成功",
    )


@router.post("/media/upload-video", response_model=Dict[str, Any])
async def upload_video(
    file: UploadFile = File(...),
    biz_type: str = Form("general"),
    biz_id: int = Form(0),
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
) -> Dict[str, Any]:
    if file.content_type not in ALLOWED_VIDEO_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的视频类型")

    ext = VIDEO_MIME_TO_EXT[file.content_type]
    name = f"video_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{hashlib.sha1(os.urandom(16)).hexdigest()[:8]}{ext}"
    target = _uploads_dir() / name
    file_size, header = await _save_upload_file(file, target, MAX_VIDEO_SIZE_BYTES)
    if not _validate_magic(file.content_type, header):
        if target.exists():
            target.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件内容与类型不匹配")

    row = MediaFile(
        biz_type=biz_type,
        biz_id=biz_id,
        file_type="video",
        storage_path=str(target),
        file_name=file.filename or name,
        content_type=file.content_type,
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return create_response(
        data={"id": row.id, "file_name": row.file_name, "file_url": f"/uploads/{name}", "file_type": row.file_type},
        message="视频上传成功",
    )


@router.get("/media/{media_id}", response_model=Dict[str, Any])
async def get_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Member = Depends(get_current_user),
    _: Any = None,
) -> Dict[str, Any]:
    # Backward-compatible fallback for direct function calls in legacy tests.
    actor: Any = _ if _ is not None else current_user
    if not hasattr(actor, "id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证用户")

    row = (await db.execute(select(MediaFile).where(MediaFile.id == media_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="媒体不存在")
    actor_role = getattr(actor, "role", UserRole.MEMBER)
    if row.uploaded_by != actor.id and actor_role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该媒体")

    file_url = None
    if row.storage_path:
        file_url = f"/uploads/{Path(row.storage_path).name}"

    return create_response(
        data={
            "id": row.id,
            "biz_type": row.biz_type,
            "biz_id": row.biz_id,
            "file_type": row.file_type,
            "file_name": row.file_name,
            "file_url": file_url,
            "file_size": row.file_size,
            "watermark_payload": row.watermark_payload,
        },
        message="获取媒体成功",
    )
