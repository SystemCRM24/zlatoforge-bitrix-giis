from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения"""
    model_config = SettingsConfigDict(extra='ignore')

    DEBUG: int


settings = Settings()       # type: ignore
