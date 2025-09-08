from fastapi import FastAPI

from src.common import router as common_router


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
app.include_router(common_router)
