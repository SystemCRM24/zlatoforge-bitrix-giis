from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common import router as common_router
from src.test import router as test_router
from src.services import on_startup


description = """Предоставляет методы для отправки и получения запросов в ГИИС ДМДК.
Содержит полную логику этого процесса:
1) Добавление подписи в SOAP-сообщение.
2) Отправка SOAP-сообщения в ГИИС-ДМДК
3) Проверка валидности сообщения от ГИИС-ДМДК
4) Ряд утилитарных методов для работы с подписями, шифрованием и тп.
"""

app = FastAPI(
    title='Cypher',
    summary='Интерфейс для отправки SOAP-запросов в ГИИС.',
    description=description
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_event_handler('startup', on_startup)


app.include_router(common_router)
# Оставлю тут тестовые роутеры, как напоминания о страданиях))
app.include_router(test_router)
