from fastapi import APIRouter

from .clients import router as clients_router
from .examples import router as examples_router


api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(clients_router)


router = APIRouter(prefix="")
router.include_router(api_router)
router.include_router(examples_router)
