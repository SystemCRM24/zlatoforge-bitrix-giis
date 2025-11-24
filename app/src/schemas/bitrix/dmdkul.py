from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class DMDKULSchema(BaseModel):
    """Универсальный список, который описывает дмдк, его начальное состояние."""

    model_config = ConfigDict(extra="ignore")

    ID: str
    NAME: str
    UL_TYPE: str = Field(alias="PROPERTY_920", default="")
    METAL_TYPE: str = Field(alias="PROPERTY_968", default="")
    HALLMARK: str = Field(alias="PROPERTY_970", default="")  # Проба
    COMMON_WEIGHT: str = Field(alias="PROPERTY_972", default="")
    WEIGHT: str = Field(alias="PROPERTY_974", default="")
    HCM: str = Field(alias="PROPERTY_976", default="")
    QUANTITY: str = Field(alias="PROPERTY_978", default="")
    AMOUNT: str = Field(alias="PROPERTY_264", default="")

    @field_validator(
        "METAL_TYPE",
        "HALLMARK",
        "COMMON_WEIGHT",
        "WEIGHT",
        "HCM",
        "QUANTITY",
        "UL_TYPE",
        "AMOUNT",
        mode="before",
    )
    @classmethod
    def validate_dict_values(cls, value: dict) -> str:
        """Информация из полей приходит в виде словаря, который нужно разбирать"""
        for val in value.values():
            return val
        return ""

    @computed_field
    @property
    def OKPD_CODE(self) -> str:
        """Код ОКПД"""
        match self.METAL_TYPE:
            case "Золото":
                return "38.32.21.110"
            case "Серебро":
                return "38.32.21.120"
            case "Платина":
                return "38.32.21.130"
            case "Палладий":
                return "38.32.21.132"
        return ""

    @computed_field
    @property
    def DMDK_METAL_TYPE(self) -> str:
        """Код металла из ДМДК"""
        match self.METAL_TYPE:
            case "Золото":
                return "DM_GOLD"
            case "Серебро":
                return "DM_SILVER"
            case "Платина":
                return "DM_PLATINUM"
            case "Палладий":
                return "DM_PALLADIUM"
        return ""

    @computed_field
    @property
    def COMMON_WEIGHT_EXP(self) -> str:
        """Общий вес в граммах выраженный в единицах измерения ДМДК"""
        return self.grm_to_dmdk_exp(self.COMMON_WEIGHT)

    @computed_field
    @property
    def HCM_EXP(self) -> str:
        """Чистая химическая масса в граммах выраженный в единицах измерения ДМДК"""
        return self.grm_to_dmdk_exp(self.HCM)

    @staticmethod
    def grm_to_dmdk_exp(weight: str) -> str:
        """Переводим граммы в милиграммы"""
        if weight:
            return str(int(float(weight) * 1e5))
        return "0"

    @computed_field
    @property
    def AMOUNT_EXP(self) -> str:
        """Возвращаем сумму партии в единицах измерения ДМДК"""
        if self.AMOUNT:
            return str(int(float(self.AMOUNT) * 1e4))
        return "0"

    @computed_field
    @property
    def HALLMARK_EXP(self) -> str:
        """Проба в единицах измерения ДМДК"""
        if self.HALLMARK:
            return str(int(float(self.HALLMARK) * 1e2))
        return "0"
