"""
任务路由聚合（兼容旧引用）。
"""

from fastapi import APIRouter

from .repair import router as repair_router
from .monitoring import router as monitoring_router
from .assistance import router as assistance_router
from .coop import router as coop_router
from .inspection_sampling import router as inspection_sampling_router
from .task_lifecycle import router as task_lifecycle_router
from .repair_orders import router as repair_orders_router
from .media import router as media_router

router = APIRouter()
router.include_router(repair_router)
router.include_router(monitoring_router)
router.include_router(assistance_router)
router.include_router(coop_router)
router.include_router(inspection_sampling_router)
router.include_router(task_lifecycle_router)
router.include_router(repair_orders_router)
router.include_router(media_router)
