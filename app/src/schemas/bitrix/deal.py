from pydantic import BaseModel, ConfigDict


class DealSchema(BaseModel):
    """Схема для сделки"""

    model_config = ConfigDict(extra="ignore")

    ID: str
    TITLE: str
    CONTACT_ID: str
