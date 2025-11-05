from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src._examples import router as test_router
from src.services import on_startup


description = """Предоставляет методы для отправки и получения запросов в ГИИС ДМДК.
Содержит полную логику этого процесса:
1) Добавление подписи в SOAP-сообщение.
2) Отправка SOAP-сообщения в ГИИС-ДМДК
3) Проверка валидности сообщения от ГИИС-ДМДК
4) Ряд утилитарных методов для работы с подписями, шифрованием и тп.
"""

app = FastAPI(
    title="Cypher", summary="Интерфейс для отправки SOAP-запросов в ГИИС.", description=description
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_event_handler("startup", on_startup)

# роуты
app.include_router(test_router)  # Оставлю тут тестовые роутеры, как напоминания о страданиях))


@app.get("/ping", status_code=200)
async def ping() -> str:
    """pong da best"""
    return "Pong"
