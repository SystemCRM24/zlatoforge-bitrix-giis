from datetime import datetime

from src.schemas.bitrix import BitrixContact


class ServiceException(Exception):
    """Кастомное исключение сервиса"""


class ServiceValidator:
    """Осуществляем валидацию различных сущностей."""

    @staticmethod
    def check_birthdate(contact: BitrixContact) -> bool:
        """Проверка заполненности поля даты рождения."""
        if not isinstance(contact.birth_date, datetime):
            msg = (
                f"Необходимо указать дату рождения клиента {contact.last_name} {contact.name} для "
                "осуществления проверки в реестрах Росфинмониторинга"
            )
            raise ServiceException(msg)
        return True

    @staticmethod
    def check_passport_data(contact: BitrixContact) -> bool:
        """Проверка заполнненности паспортных данных."""
        result = all((
            contact.passport_serial,
            contact.passport_number,
            contact.passport_issuer,
            contact.passport_issue_date,
        ))
        if not result:
            msg = (
                f"Необходимо заполнить все паспортные данные клиента {contact.last_name} "
                f"{contact.name}: серия и номер паспорта, кем выдан и дата выдачи, "
                "для осуществления проверки в реестрах Росфинмониторинга"
            )
            raise ServiceException(msg)
        return result
