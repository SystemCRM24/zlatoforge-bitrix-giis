from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BitrixClient(BaseModel):
    """Представление клиента"""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(alias="ID")
    name: str = Field(alias="NAME")
    last_name: str = Field(alias="LAST_NAME")
    birth_date: datetime | None = Field(alias="BIRTHDATE")
    # Паспортные данные
    passport_serial: str = Field(alias="UF_CRM_1648298974485")
    passport_number: str = Field(alias="UF_CRM_1648298987071")
    passport_issuer: str = Field(alias="UF_CRM_1648299575558")
    passport_issue_date: datetime | None = Field(alias="UF_CRM_1648299623368")

    def check_passport_data(self) -> bool:
        """Проверяем паспортные данные на полноту заполнения"""
        return all((
            self.passport_serial,
            self.passport_number,
            self.passport_issuer,
            self.passport_issue_date,
        ))

    @field_validator("birth_date", "passport_issue_date", mode="before")
    @classmethod
    def validate_date(cls, birth_date: str) -> datetime | None:
        """Валидация даты дня рождения"""
        if birth_date:
            return datetime.fromisoformat(birth_date)
