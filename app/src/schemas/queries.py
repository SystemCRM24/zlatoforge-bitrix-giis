from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuerySchema(BaseModel):
    """Базовая схема для валидации query параметров."""

    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(
        default="7780",
        description="Пользователь, которому будет отправлено уведомление. По умолчанию Админ Мега.",
    )
    contour: str = Field(default="test", description="Используемый контур в ГИИС.")

    @field_validator("contour", mode="before")
    @classmethod
    def validate_contour(cls, value: str) -> str:
        """Валидация контуров."""
        if value == "Рабочий" or value == "work":
            return "work"
        return "test"


class ReceiptQuerySchema(QuerySchema):
    """Схема для валидации query параметров для создания квитанций."""

    deal_id: str = Field(description="Идентификатор сделки в Битриксе.")


class ContactQuerySchema(QuerySchema):
    """Схема для валидации query параметров для проверки контактов."""

    contact_id: str = Field(description="Идентификатор контакта в Битриксе.")
