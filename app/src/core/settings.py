from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения"""

    model_config = SettingsConfigDict(extra="ignore")

    MODE: str

    # Для работы с контурами ГИИС
    @property
    def _giis_work_contour(self) -> str:
        """Возвращает адрес рабочего контура ГИИС"""
        return "http://0.0.0.0:1500/ws/v3/"
    
    @property
    def _giis_test_contour(self) -> str:
        """Возвращает адрес тестового контура ГИИС"""
        return "http://0.0.0.0:1501/ws/v3/"
    
    @property
    def GIIS_CONTOUR(self) -> str:
        """Возвращает контур в зависимости от режима работы приложения."""
        if self.MODE == 'prod':
            return self._giis_work_contour
        return self._giis_test_contour


settings = Settings()  # type: ignore
