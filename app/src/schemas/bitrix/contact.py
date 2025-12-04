from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContactSchema(BaseModel):
    """Представление клиента"""

    model_config = ConfigDict(extra="ignore")

    ID: str
    NAME: str
    LAST_NAME: str
    SECOND_NAME: str = Field(default="")
    BIRTHDATE: date | None = None
    ADDRESS: str = Field(alias="UF_CRM_1591111034541", default="")
    # Паспортные данные
    PASSPORT_SERIAL: str = Field(alias="UF_CRM_1648298974485", default="")
    PASSPORT_NUMBER: str = Field(alias="UF_CRM_1648298987071", default="")
    PASSPORT_ISSUER: str = Field(alias="UF_CRM_1648299575558", default="")
    PASSPORT_ISSUE_DATE: date | None = Field(alias="UF_CRM_1648299623368", default=None)

    @field_validator("BIRTHDATE", "PASSPORT_ISSUE_DATE", mode="before")
    @classmethod
    def validate_date(cls, birth_date: str) -> date | None:
        """Валидация даты дня рождения"""
        if birth_date:
            return datetime.fromisoformat(birth_date).date()

    @field_validator("ADDRESS", mode="after")
    @classmethod
    def cleanup_address(cls, address: str) -> str:
        """Очистка адреса от лишних символов."""
        pattern = "|;"
        result = address.split(pattern)[0]
        return result
