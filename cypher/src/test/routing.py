from fastapi import APIRouter

from .try1 import router as router1
from .try2 import router as router2
from .try3 import router as router3


router = APIRouter(prefix='/tests')
router.include_router(router1)
router.include_router(router2)
router.include_router(router3)
