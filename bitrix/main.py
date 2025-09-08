from fastapi import FastAPI

from src.common import router as common_router


app = FastAPI(
    title="Bitrix",
    summary="Приложение для работы с битриксом Златокузницы."
)
app.include_router(common_router)
