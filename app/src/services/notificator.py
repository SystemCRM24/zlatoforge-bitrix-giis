import asyncio

from src.bitrix import BitrixRepository as BXR


class Notificator:
    """Класс для отправки уведомлений пользователям."""

    @staticmethod
    def send_message(user_id: str | None, message: str) -> None:
        """Отправляем уведомление пользователю."""
        asyncio.create_task(BXR.send_notification(message, user_id))

    @staticmethod
    def send_check_rfm(user_id: str | None, client: str) -> None:
        """Отправить сообщение для проверки клиента в реестрах РФМ."""
        ntf = f"Осуществляется проверка клиента {client} в реестрах Росфинмониторинга."
        Notificator.send_message(user_id, ntf)

    @staticmethod
    def send_check_rfm_result(user_id: str | None, client: str, result: str) -> None:
        """Отправить уведомление о результатах проверки"""
        ntf = f"Клиент {client} проверен.\nСтатус: {result}"
        Notificator.send_message(user_id, ntf)

    @staticmethod
    def send_create_scrap_receipt(user_id: str | None, client: str) -> None:
        """Отправить уведомление о создании чека"""
        ntf = f"Осуществляется создание чека для клиента {client} на скупку лома."
        Notificator.send_message(user_id, ntf)
