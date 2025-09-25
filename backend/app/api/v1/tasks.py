"""
任务路由聚合（兼容旧引用）。
"""

from fastapi import APIRouter

from .repair import router as repair_router
from .monitoring import router as monitoring_router
from .assistance import router as assistance_router

router = APIRouter()
router.include_router(repair_router)
router.include_router(monitoring_router)
router.include_router(assistance_router)
