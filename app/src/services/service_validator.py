from datetime import date
from typing import Literal

from src.schemas.bitrix import ContactSchema, DMDKULSchema


class ServiceException(Exception):
    """Кастомное исключение сервиса"""


class ServiceValidator:
    """Осуществляем валидацию различных сущностей."""

    @staticmethod
    def check_birthdate(contact: ContactSchema) -> bool:
        """Проверка заполненности поля даты рождения."""
        if not isinstance(contact.BIRTHDATE, date):
            msg = (
                f"Необходимо указать дату рождения клиента {contact.LAST_NAME} {contact.NAME} для "
                "осуществления проверки в реестрах Росфинмониторинга"
            )
            raise ServiceException(msg)
        return True

    @staticmethod
    def check_passport_data(contact: ContactSchema, reason: Literal["check", "scrap"]) -> bool:
        """Проверка заполнненности паспортных данных."""
        result = all((
            contact.PASSPORT_SERIAL,
            contact.PASSPORT_NUMBER,
            contact.PASSPORT_ISSUER,
            contact.PASSPORT_ISSUE_DATE,
        ))
        if not result:
            if reason == "scrap":
                pre = "Для создания квитанциии на скупку "
            else:
                pre = "Для проверки в реестрах Росфинмониторинга "
            msg = (
                f"{pre} необходимо заполнить все паспортные данные клиента {contact.LAST_NAME} "
                f"{contact.NAME}: серия и номер паспорта, кем выдан и дата выдачи."
            )
            raise ServiceException(msg)
        return result

    @staticmethod
    def check_contact_address(contact: ContactSchema) -> bool:
        """Проверка заполненности адреса."""
        if not contact.ADDRESS:
            raise ServiceException("Для создания квитанции необходимо заполнить адрес клиента.")
        return True

    @staticmethod
    def check_dmdkul_element(dmdkuls: list[DMDKULSchema]) -> bool:
        """Проверяем списочные элементы на присутствие в них галочки: Интеграция с ГИИС"""
        for el in dmdkuls:
            if el.IS_GIIS_INTEGRATION:
                return True
        raise ServiceException(
            'В списочных элементах не найдено ни одного с пометкой "Интеграция с ГИИС"'
        )
