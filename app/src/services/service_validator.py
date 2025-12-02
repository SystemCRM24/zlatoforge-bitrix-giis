from datetime import date

from src.schemas.bitrix import ContactSchema


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
    def check_passport_data(contact: ContactSchema) -> bool:
        """Проверка заполнненности паспортных данных."""
        result = all((
            contact.PASSPORT_SERIAL,
            contact.PASSPORT_NUMBER,
            contact.PASSPORT_ISSUER,
            contact.PASSPORT_ISSUE_DATE,
        ))
        if not result:
            msg = (
                f"Необходимо заполнить все паспортные данные клиента {contact.LAST_NAME} "
                f"{contact.NAME}: серия и номер паспорта, кем выдан и дата выдачи, "
                "для осуществления проверки в реестрах Росфинмониторинга"
            )
            raise ServiceException(msg)
        return result

    @staticmethod
    def check_contact_address(contact: ContactSchema) -> bool:
        """Проверка заполненности адреса."""
        if not contact.ADDRESS:
            raise ServiceException("Для создания квитанции необходимо заполнить адрес клиента.")
        return True
