from typing import Any, Union, Literal
from zeep import AsyncClient
from lxml import etree # type:ignore
import random
import asyncio

from .xml_message import SignedXMLMessage
from .namespaces import NS
from src.utils import logger
from src.core import settings


class DMDKHandler:
    """Обработчик запросов к ДМДК"""

    WORK_CLIENT = None
    TEST_CLIENT = None
    DMDK_HEADERS = {"Content-Type": "text/xml; charset=utf-8"}
    MAXIMUM_TRIES = 20

    def _get_soap_client(self) -> AsyncClient:
        """Из-за того, что при старте файла excnahge3.wsdl может не быть, пользуемся методом."""
        if self.__class__.TEST_CLIENT is None:
            self.__class__.TEST_CLIENT = AsyncClient('./logs/test-exchange3.wsdl')
        if self.__class__.WORK_CLIENT is None:
            self.__class__.WORK_CLIENT = AsyncClient('./logs/work-exchange3.wsdl')
        if self.contour == 'work' or settings.MODE == 'prod':
            logger.debug('DMDKHandler uses Work contour.')
            return self.__class__.WORK_CLIENT
        logger.debug('DMDKHandler uses Test contour.')
        return self.__class__.TEST_CLIENT

    def __init__(self, message: SignedXMLMessage, contour: Literal['test', 'work', 'app'] = 'app'):
        """
        contour - контур, который будет учавствовать в запросах. 
        Если явно не определн test или work - выбирается в зависимости от режима прилоожения.
        """
        self.message = message
        self.contour = contour
        self.response: Any = None
    
    def _setup_post_request(self, message: str) -> dict:
        """Возвращает настройки для соап-запроса"""
        address = settings._giis_test_contour
        if self.contour == 'work' or settings.MODE == 'prod':
            address = settings._giis_work_contour
        return {'address': address, 'message': message, 'headers': self.DMDK_HEADERS}
        
    async def process(self, await_check_result=False) -> dict:
        """
        Отправляет собранный запрос и парсит ответ и превращает его в словарь
        Флаг await_check_result нужен для того, чтобы дождаться результата check запроса. 
        Сервер может его вернуть не сразу.
        """
        self.message.sign()
        message_str = self.message.to_string()
        client = self._get_soap_client()
        attempt = 1
        is_check_method = self.message.endpoint.startswith('Check')
        status = content = None
        logger.debug(f'Trying to fetch data from DMDK API, method = {self.message.endpoint}')
        with client.settings(raw_response=True):
            while attempt < self.MAXIMUM_TRIES:
                response = await client.transport.post(**self._setup_post_request(message_str))
                content = etree.fromstring(response.content)
                status = content.find(f'.//{{{NS}}}status')
                if not await_check_result or not is_check_method:
                    break
                response_data = content.find(f'.//{{{NS}}}ResponseData')
                if len(response_data) > 2 or status.text == 'PREPARED':
                    break
                logger.debug(f'Waiting for resonse DMDK API, attempts = {attempt}')
                attempt += 1
                await asyncio.sleep(random.random())
        self.response = content
        status_text = status.text if status is not None else None
        logger.success(f'Data from DMDK API received, status = {status_text}')
        return self.response

    def create_check_request(self) -> Union['DMDKHandler', None]:
        """Фабрика для выполнения Check - запросов. Вернет новый объект DMDKHandler."""
        is_send_method = self.message.endpoint.startswith('Send')
        message_id_node = self.response.find(f'.//{{{NS}}}messageId')
        message_id = message_id_node is not None and message_id_node.text
        if not all((is_send_method, message_id)):
            return 
        endpoint = f'Check{self.message.endpoint[4:]}'
        check_message = SignedXMLMessage(endpoint, NS)
        message_id_node = etree.SubElement(check_message.request_data, f'{{{NS}}}messageId')
        message_id_node.text = message_id
        return DMDKHandler(check_message)
