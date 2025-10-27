from fastapi import APIRouter

from .try1 import router as router1
from .try2 import router as router2
from .try3 import router as router3
from .try4 import router as router4
from .try5 import router as router5


router = APIRouter(prefix='/tests', tags=['tests'])
router.include_router(router1)
router.include_router(router2)
router.include_router(router3)
router.include_router(router4)
router.include_router(router5)
