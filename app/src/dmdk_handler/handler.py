import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from lxml import etree  # type:ignore
from zeep import AsyncClient

from src.core import settings
from src.utils import logger

from .namespaces import NS
from .xml_message import SignedXMLMessage


class DMDMKHandlerException(Exception):
    """Кастомный тип исключений для обработчика."""


class DMDKHandler:
    """Обработчик запросов к ДМДК"""

    WORK_CLIENT = None
    TEST_CLIENT = None
    DMDK_HEADERS = {"Content-Type": "text/xml; charset=utf-8"}
    MAXIMUM_TRIES = 30
    TIME_PATTERN = "%Y-%m-%d %H-%M-%S-%f"
    LOCK = asyncio.Lock()

    def _get_soap_client(self) -> AsyncClient:
        """Из-за того, что при старте файла excnahge3.wsdl может не быть, пользуемся методом."""
        if self.__class__.TEST_CLIENT is None:
            self.__class__.TEST_CLIENT = AsyncClient("./logs/test-exchange3.wsdl")
        if self.__class__.WORK_CLIENT is None:
            self.__class__.WORK_CLIENT = AsyncClient("./logs/work-exchange3.wsdl")
        if self.contour == "work" or settings.MODE == "prod":
            logger.debug("DMDKHandler uses Work contour.")
            return self.__class__.WORK_CLIENT
        logger.debug("DMDKHandler uses Test contour.")
        return self.__class__.TEST_CLIENT

    def __init__(
        self, message: SignedXMLMessage, contour: Literal["test", "work", "app"] = "app", log=False
    ):
        """
        contour - контур, который будет учавствовать в запросах.
        Если явно не определн test или work - выбирается в зависимости от режима прилоожения.
        """
        self.message = message
        self.contour = contour
        self.log = log
        self._requested_at = None
        self.response: Any = None

    def _setup_post_request(self, message: str) -> dict:
        """Возвращает настройки для соап-запроса"""
        address = settings._giis_test_contour
        if self.contour == "work" or settings.MODE == "prod":
            address = settings._giis_work_contour
        return {"address": address, "message": message, "headers": self.DMDK_HEADERS}

    async def process(self, await_check_result=False) -> Any:
        """
        Отправляет собранный запрос и парсит ответ и превращает его в словарь
        Флаг await_check_result нужен для того, чтобы дождаться результата check запроса.
        Сервер может его вернуть не сразу.
        """
        if self._requested_at is None:
            self._requested_at = datetime.now(settings.TIME_ZONE)
        self.message.sign()
        if self.log:
            asyncio.create_task(self._log_message())
        message_str = self.message.to_string()
        client = self._get_soap_client()
        attempt = 1
        is_check_method = self.message.endpoint.startswith("Check")
        status = content = None
        logger.debug(f"Trying to fetch data from DMDK API, method = {self.message.endpoint}")
        with client.settings(raw_response=True):
            while attempt < self.MAXIMUM_TRIES:
                async with self.LOCK:
                    response = await client.transport.post(**self._setup_post_request(message_str))
                content = etree.fromstring(response.content)
                status = content.find(f".//{{{NS}}}status")
                if not await_check_result or not is_check_method:
                    break
                response_data = content.find(f".//{{{NS}}}ResponseData")
                if len(response_data) > 2 or status.text == "PREPARED":
                    break
                logger.debug(
                    f"Waiting for resonse DMDK API status = {status.text}, attempts = {attempt}"
                )
                delay = random.random() * 2
                await asyncio.sleep(delay)
                attempt += 1
        self.response = content
        if self.log:
            asyncio.create_task(self._log_response())
        status_text = status.text if status is not None else None
        self._check_validation_fault()
        self._check_inner_dmdk_exception()
        logger.success(f"Data from DMDK API received, status = {status_text}")
        return self.response

    def _make_log_path(self) -> str:
        """Возвращает патч до логов"""
        time = self._requested_at.strftime(self.TIME_PATTERN)  # type:ignore
        path = f"./logs/{time}"
        Path(path).mkdir(exist_ok=True)
        prefix = "send" if self.message.endpoint.startswith("Send") else "check"
        return f"{path}/{prefix}"

    async def _log_message(self):
        """логаем сообщение для ДМДК"""
        path = self._make_log_path()
        with open(f"{path}-request.xml", mode="wb") as file:
            file.write(self.message.to_bytes(True))

    async def _log_response(self):
        """Логаем ответ от ДМДК"""
        path = self._make_log_path()
        with open(f"{path}-response.xml", mode="wb") as file:
            file.write(etree.tostring(self.response, pretty_print=True, encoding="utf-8"))

    def _check_validation_fault(self) -> bool:
        """Проверяем ответ от ДМДК на предмет правильности заполнения сообщения и типов данных."""
        error_detail_type_node = self.response.xpath("//*[local-name() = 'ErrorDetailType']")
        if not error_detail_type_node:
            return True
        error_detail_type_node = error_detail_type_node[0]
        code_node = error_detail_type_node.find(f".//{{{NS}}}code")
        msg_node = error_detail_type_node.find(f".//{{{NS}}}msg")
        raise DMDMKHandlerException(f"Code={code_node.text}\nmsg={msg_node.text}")

    def _check_inner_dmdk_exception(self) -> bool:
        """поиск внутренней ошибки ДМДК"""
        # failure_node = self.response.xpath("//*[local-name() = 'ErrorDetailType']")
        failure_node = self.response.find(f".//{{{NS}}}failure")
        if not failure_node:
            return True
        error_node = failure_node.find(f".//{{{NS}}}error")
        code_node = error_node.find(f".//{{{NS}}}code")
        msg_node = error_node.find(f".//{{{NS}}}msg")
        raise DMDMKHandlerException(f"Code={code_node.text}\nmsg={msg_node.text}")

    def create_check_request(self) -> "DMDKHandler":
        """
        Фабрика для выполнения Check - запросов. Вернет новый объект DMDKHandler
        в котором все атрибуты наследуются от текущего объекта.
        """
        if not self.message.endpoint.startswith("Send"):
            raise AttributeError(
                f'Failed to create "Check..." handler. {self.message.endpoint} doesn\'t Send...'
            )
        message_id_node = self.response.find(f".//{{{NS}}}messageId")
        message_id = message_id_node is not None and message_id_node.text
        if not message_id:
            raise AttributeError(f'Failed to create "Check..." handler. {message_id=} is invalid.')
        endpoint = f"Check{self.message.endpoint[4:]}"
        check_message = SignedXMLMessage(endpoint, NS)
        message_id_node = etree.SubElement(check_message.request_data, f"{{{NS}}}messageId")
        message_id_node.text = message_id
        handler = DMDKHandler(check_message)
        handler.contour = self.contour
        handler.log = self.log
        handler._requested_at = self._requested_at
        return handler

    def response_to_list(self) -> list:
        """Возвращает респонс в виде списка. Используется для отладки."""
        response_data = self.response.xpath("//*[local-name() = 'ResponseData']")
        if response_data:
            response_data = response_data[0]
            response_data.tag = etree.QName(response_data).localname
            response_data.attrib.clear()
            decoded_response = etree.tostring(response_data, pretty_print=True, encoding="utf-8")
            return decoded_response.decode().split("\n")
        return []
