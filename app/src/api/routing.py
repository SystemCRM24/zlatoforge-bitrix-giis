from fastapi import APIRouter

from .examples import router as examples_router


router = APIRouter(prefix="/api")
router.include_router(examples_router)
