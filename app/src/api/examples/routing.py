from fastapi import APIRouter

from .example1 import router as e1_router
from .example2 import router as e2_router


router = APIRouter(prefix="/examples", tags=["examples"])
router.include_router(e1_router)
router.include_router(e2_router)
