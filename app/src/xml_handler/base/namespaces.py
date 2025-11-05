class NS:
    """Содержит в себе константы для объявления неймспейсов в сообщении"""

    # Корневые пространства имен.
    soapenv = "http://schemas.xmlsoap.org/soap/envelope/"
    ns = "urn://xsd.dmdk.goznak.ru/exchange/3.0"
    ds = "http://www.w3.org/2000/09/xmldsig#"  # Специфичный неймспейс. Нужен для подписи.

    # Пользовательские пространсва имен.
    contractor = "urn://xsd.dmdk.goznak.ru/contractor/3.0"
    deal = "urn://xsd.dmdk.goznak.ru/deal/3.0"
    types = "urn://xsd.dmdk.goznak.ru/types/3.0"
