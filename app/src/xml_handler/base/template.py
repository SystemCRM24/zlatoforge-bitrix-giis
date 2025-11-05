from .namespaces import NS


class XMLTemplate:
    """
    Базовый класс для сборки XML-сообщения для ГИИС-ДМДК.
    Предоставляет общий интерфейс работы с XML-сообщениями.
    """

    NAMAP = {"soapenv": NS.soapenv, "ns": NS.ns}
    REQUEST_DATA_TAG = "request_data"

    @classmethod
    def build(cls):
        """Метод для сборки сообщения"""
        pass
