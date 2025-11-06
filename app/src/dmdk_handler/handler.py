from zeep import AsyncClient

from .node import Node
from .xml_message import SignedXMLMessage


class DMDKHandler:
    """Обработчик запросов к ДМДК"""

    SOAP_CLIENT = None

    @classmethod
    def _get_soap_client(cls) -> AsyncClient:
        """Из-за того, что при старте файла excnahge3.wsdl может не быть, пользуемся методом."""
        if cls.SOAP_CLIENT is None:
            cls.SOAP_CLIENT = AsyncClient("./logs/exchange3.wsdl")
        return cls.SOAP_CLIENT

    def __init__(self, endpoint: str, request_data: Node) -> None:
        self.message = SignedXMLMessage(endpoint, request_data)
        self.response = {}

    async def process(self) -> dict:
        """Отправляет собранный запрос и парсит ответ и превращает его в словарь"""
        self.message.build()
        raw_response = await self._do_request()
        return self._parse_response(raw_response)

    async def _do_request(self):
        """Отправляет запрос и возвращает разпарсенный документ"""
        client = self._get_soap_client()
        with client.settings(raw_response=True):
            response = await client.transport.post(
                address="http://0.0.0.0:1500/ws/v3/",
                message=self.message.to_string(),
                headers={"Content-Type": "text/xml; charset=utf-8"},
            )
        return response.content

    def _parse_response(self, response) -> dict:
        """Парсит сообщение и превращает его в словарь."""
        return self.response
