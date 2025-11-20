from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BitrixContact(BaseModel):
    """Представление клиента"""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(alias="ID")
    name: str = Field(alias="NAME")
    last_name: str = Field(alias="LAST_NAME")
    birth_date: datetime | None = Field(alias="BIRTHDATE", default=None)
    # Паспортные данные
    passport_serial: str = Field(alias="UF_CRM_1648298974485", default="")
    passport_number: str = Field(alias="UF_CRM_1648298987071", default="")
    passport_issuer: str = Field(alias="UF_CRM_1648299575558", default="")
    passport_issue_date: datetime | None = Field(alias="UF_CRM_1648299623368", default=None)

    @field_validator("birth_date", "passport_issue_date", mode="before")
    @classmethod
    def validate_date(cls, birth_date: str) -> datetime | None:
        """Валидация даты дня рождения"""
        if birth_date:
            return datetime.fromisoformat(birth_date)
