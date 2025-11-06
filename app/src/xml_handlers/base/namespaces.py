# Корневые неймспейсы
SOAPENV = "http://schemas.xmlsoap.org/soap/envelope/"
NS = "urn://xsd.dmdk.goznak.ru/exchange/3.0"
# Адресные неймспейсы
CONTRACTOR = "urn://xsd.dmdk.goznak.ru/contractor/3.0"
DEAL = "urn://xsd.dmdk.goznak.ru/deal/3.0"
TYPES = "urn://xsd.dmdk.goznak.ru/types/3.0"


class NSBuilder:
    """Собирает пространства имен в обшую структуру"""

    __slots__ = ("map", "urls")

    def __init__(self, *urls: str) -> None:
        """Сюда нужно передать урлы пространств имен для запроса."""
        # Корневые пространства имён.
        self.map = {"soapenv": SOAPENV, "ns": NS}
        self.urls = {SOAPENV, NS}
        for index, value in enumerate(urls, 1):
            self.map[f"ns{index}"] = value
            self.urls.add(value)
