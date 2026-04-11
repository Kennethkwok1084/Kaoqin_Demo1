"""Rule-based OCR structuring service for repair orders."""

import re
from typing import Any, Dict, List


class RepairOCRService:
    """Parse OCR payload into structured repair ticket fields."""

    ISSUE_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
        "network": ["网络", "wifi", "wlan", "掉线", "无法上网", "网速", "路由"],
        "power": ["断电", "停电", "电源", "跳闸", "供电"],
        "equipment": ["交换机", "ap", "机柜", "终端", "设备", "网线", "端口"],
    }

    PHONE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")
    ROOM_RE = re.compile(r"(?:房间|宿舍|寝室|房号)[:：\s]*([A-Za-z0-9\-]{2,16})")
    REPAIR_NO_RE = re.compile(r"(?:报修单号|工单号|编号)[:：\s]*([A-Za-z0-9\-]{6,32})")
    NAME_RE = re.compile(r"(?:报修人|联系人|姓名)[:：\s]*([\u4e00-\u9fa5A-Za-z·]{2,20})")

    @classmethod
    def analyze(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw_payload = cls._extract_raw_payload(payload)
        text = cls._collect_text(raw_payload)

        structured_data: Dict[str, Any] = {
            "repair_no": cls._extract_repair_no(raw_payload, text),
            "report_user_name": cls._extract_name(raw_payload, text),
            "report_phone": cls._extract_phone(raw_payload, text),
            "room_no": cls._extract_room_no(raw_payload, text),
            "issue_content": cls._extract_issue_content(raw_payload, text),
            "issue_category": cls._extract_issue_category(raw_payload, text),
        }

        recognized_fields = sum(
            1
            for key in [
                "repair_no",
                "report_user_name",
                "report_phone",
                "issue_content",
                "issue_category",
            ]
            if structured_data.get(key)
        )
        confidence = round(min(1.0, recognized_fields / 5.0), 2)

        warnings: List[str] = []
        if not structured_data.get("issue_content"):
            warnings.append("未识别到问题描述")
        if not structured_data.get("report_phone"):
            warnings.append("未识别到联系电话")

        return {
            "raw_payload": raw_payload,
            "structured_data": structured_data,
            "confidence": confidence,
            "needs_manual_review": confidence < 0.6 or bool(warnings),
            "warnings": warnings,
        }

    @staticmethod
    def _extract_raw_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        value = payload.get("ocr_payload")
        return value if isinstance(value, dict) else payload

    @classmethod
    def _collect_text(cls, raw_payload: Dict[str, Any]) -> str:
        parts: List[str] = []

        for key in ["raw_text", "text", "ocr_text", "content"]:
            value = raw_payload.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())

        for key in ["lines", "blocks", "texts", "results"]:
            value = raw_payload.get(key)
            if not isinstance(value, list):
                continue
            for item in value:
                if isinstance(item, str) and item.strip():
                    parts.append(item.strip())
                elif isinstance(item, dict):
                    text = item.get("text") or item.get("content")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())

        return "\n".join(parts)

    @classmethod
    def _extract_phone(cls, raw_payload: Dict[str, Any], text: str) -> str | None:
        for key in ["report_phone", "reportPhone", "phone", "mobile"]:
            value = raw_payload.get(key)
            if isinstance(value, str):
                matched = cls.PHONE_RE.search(value)
                if matched:
                    return matched.group(1)

        matched = cls.PHONE_RE.search(text)
        return matched.group(1) if matched else None

    @classmethod
    def _extract_repair_no(cls, raw_payload: Dict[str, Any], text: str) -> str | None:
        for key in ["repair_no", "repairNo", "ticket_no", "ticketNo", "work_order_no"]:
            value = raw_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:64]

        matched = cls.REPAIR_NO_RE.search(text)
        return matched.group(1)[:64] if matched else None

    @classmethod
    def _extract_name(cls, raw_payload: Dict[str, Any], text: str) -> str | None:
        for key in ["report_user_name", "reportUserName", "name", "contact_name", "contactName"]:
            value = raw_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:64]

        matched = cls.NAME_RE.search(text)
        return matched.group(1)[:64] if matched else None

    @classmethod
    def _extract_room_no(cls, raw_payload: Dict[str, Any], text: str) -> str | None:
        for key in ["room_no", "roomNo", "dorm_room_no", "dormRoomNo"]:
            value = raw_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:32]

        matched = cls.ROOM_RE.search(text)
        return matched.group(1)[:32] if matched else None

    @staticmethod
    def _extract_issue_content(raw_payload: Dict[str, Any], text: str) -> str | None:
        for key in ["issue_content", "issueContent", "problem", "description", "fault_desc"]:
            value = raw_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:1000]

        if text.strip():
            return text.strip()[:1000]
        return None

    @classmethod
    def _extract_issue_category(cls, raw_payload: Dict[str, Any], text: str) -> str:
        for key in ["issue_category", "issueCategory", "category"]:
            value = raw_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:64]

        lowered = text.lower()
        for category, keywords in cls.ISSUE_CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in lowered:
                    return category
        return "other"
