from pydantic import BaseModel, ConfigDict, Field, field_validator


class DMDKSmartProcessSchema(BaseModel):
    """Смарт-процесс описывающий единицу драгоценного металла или камня"""

    model_config = ConfigDict(extra="ignore")

    ID: str = Field(alias="id")
    TITLE: str = Field(alias="title")

    @field_validator("ID", mode="before")
    @classmethod
    def validate_id(cls, id: int) -> str:
        """Приводим все инты к строкам"""
        return str(id)
