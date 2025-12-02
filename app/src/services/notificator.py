import asyncio
from typing import Literal

from src.bitrix import BitrixRepository as BXR
from src.utils import logger


class Notificator:
    """Класс для отправки уведомлений пользователям."""

    @staticmethod
    def send_message(
        user_id: str | None, message: str, log: Literal["info", "success", "warning"] = "info"
    ) -> None:
        """Отправляем уведомление пользователю."""
        asyncio.create_task(BXR.send_notification(message, user_id))
        method = getattr(logger, log, None)
        if method:
            method(message)

    @staticmethod
    def send_check_rfm(user_id: str | None, client: str) -> None:
        """Отправить сообщение для проверки клиента в реестрах РФМ."""
        msg = f"Осуществляется проверка клиента {client} в реестрах Росфинмониторинга."
        Notificator.send_message(user_id, msg)

    @staticmethod
    def send_check_rfm_result(user_id: str | None, client: str, result: str) -> None:
        """Отправить уведомление о результатах проверки"""
        msg = f"Клиент {client} проверен.\nСтатус: {result}"
        Notificator.send_message(user_id, msg, "success")

    @staticmethod
    def send_create_scrap_receipt(user_id: str | None, deal_id: str) -> None:
        """Отправить уведомление о создании квитанцииц На скупку лома."""
        msg = f"Осуществляется создание квитанции по сделке #{deal_id} на скупку лома."
        Notificator.send_message(user_id, msg)

    @staticmethod
    def send_create_receipt_result(user_id: str | None, receipt_id: str) -> None:
        """Успешное создание квитанции"""
        msg = f"Квитанция #{receipt_id} успешно создана."
        Notificator.send_message(user_id, msg, "success")

    @staticmethod
    def add_scrap_to_receipt_result(user_id: str | None, receipt_id: str) -> None:
        """Отправить уведомление о успехе добавления позиций в квитанцию"""
        msg = f"Позиции лома из сделки успешно добавлены в квитанцию {receipt_id}"
        Notificator.send_message(user_id, msg, "success")

    @staticmethod
    def send_create_production_receipt(user_id: str | None, deal_id: str) -> None:
        """Отправить уведомление о создании квитанции на изготовление юи"""
        msg = f"Осушествляется создание квитанции по сделке #{deal_id} на изготовление юи."
        Notificator.send_message(user_id, msg)
