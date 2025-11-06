import base64

import pycades  # type:ignore
from lxml import etree  # type:ignore
from zeep import AsyncClient

from .gost_xml_transform.gost_xml_transform import GOSTXMLTransform
from .namespaces import NSBuilder
from .node import Node


REQUEST_DATA_TAG = "RequestData"
# Константы, необходимые для подписи.
DSMAP = {"ds": "http://www.w3.org/2000/09/xmldsig#"}  # Специфичный неймспейс. Нужен для подписи.
DS_PREFIX = f"{{{DSMAP['ds']}}}"
C14N_TRANSFORM = "http://www.w3.org/2001/10/xml-exc-c14n#"
SMEV_TRANSFORM = "urn://smev-gov-ru/xmldsig/transform"
SIGNATURE_METHOD = "urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34102012-gostr34112012-256"
DIGEST_METHOD = "urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-256"
# Для pycades
STORE = pycades.Store()
STORE.Open(
    pycades.CADESCOM_CONTAINER_STORE,
    pycades.CAPICOM_MY_STORE,
    pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED,
)
CERTS = STORE.Certificates
assert CERTS.Count != 0, "Certificates with private key not found"
CLIENT_CERT = CERTS.Item(1)  # У клиента он первый на очереди
SIGNER = pycades.Signer()
SIGNER.Certificate = CLIENT_CERT
SIGNER.CheckCertificate = True


class SignedXMLTemplate:
    """
    Базовый класс для сборки XML-сообщения для ГИИС-ДМДК.
    Предоставляет общий интерфейс работы с XML-сообщениями.
    """

    NS = NSBuilder()
    SOAP_CLIENT = None

    @classmethod
    def _get_soap_client(cls) -> AsyncClient:
        """Из-за того, что при старте файла excnahge3.wsdl может не быть, пользуемся методом."""
        if cls.SOAP_CLIENT is None:
            cls.SOAP_CLIENT = AsyncClient("./logs/exchange3.wsdl")
        return cls.SOAP_CLIENT

    @classmethod
    def from_node(cls, request_data: Node) -> "SignedXMLTemplate":
        """Собираем сообщениие из Node объекта."""
        obj = cls(request_data)
        obj.build_message()
        return obj

    def __init__(self, request_data: Node) -> None:
        self.request_data = request_data
        self._root_node = None

    def to_bytes(self, pretty_print=False) -> bytes:
        """Возвращает собранное сообщение в байтовом представлении"""
        if self._root_node is None:
            raise ValueError("Message is not builded. Use build_message method first.")
        return etree.tostring(self._root_node, pretty_print=pretty_print)

    def to_string(self, encoding="utf-8", pretty_print=False) -> str:
        """Возвращает собранное сообщение в строковом представлении"""
        return self.to_bytes(pretty_print).decode(encoding=encoding)

    def build_message(self):
        """Собирает xml сообщение"""
        soapenv_prefix = f"{{{self.NS.map['soapenv']}}}"
        ns_prefix = f"{{{self.NS.map['ns']}}}"
        # Собираем корневую структуру
        root_node = self._root_node = etree.Element(f"{soapenv_prefix}Envelope", nsmap=self.NS.map)
        etree.SubElement(root_node, f"{soapenv_prefix}Header")
        body_node = etree.SubElement(root_node, f"{soapenv_prefix}Body")
        request_node = etree.SubElement(body_node, f"{ns_prefix}{self.__class__.__name__}Request")
        caller_signature_node = etree.SubElement(request_node, f"{ns_prefix}CallerSignature")
        # Защищаемся от ошибок с корневой нодой
        self.request_data.name = REQUEST_DATA_TAG
        self.request_data.kwargs["id"] = REQUEST_DATA_TAG  # Наличие этого ключа обязательно
        # Заполняем данные для запроса
        request_data_node = self._fill_request_node(request_node, self.request_data)
        # Формируем подпись
        signature_node = etree.SubElement(
            caller_signature_node, f"{DS_PREFIX}Signature", nsmap=DSMAP
        )
        transformed_reference = self._transform_node(request_data_node, smev=True)
        signed_info_node = self._hash_reference(signature_node, transformed_reference)
        transformed_signed_info = self._transform_node(signed_info_node)
        self._sign_signed_info(signature_node, transformed_signed_info)
        self._insert_key_info(signature_node)

    def _fill_request_node(self, parent_xml_node, node: Node):
        """Рекурсивно заполняет parent_node значениями из node."""
        if node.namespace not in self.NS.urls:
            class_name = self.__class__.__name__
            raise AttributeError(f"Namespace={node.namespace} not specified in {class_name}.NS")
        xml_node = etree.SubElement(
            parent_xml_node, f"{{{node.namespace}}}{node.name}", **node.kwargs
        )
        if isinstance(node._value, str):
            xml_node.text = node._value
        else:
            for sub_node in node._value:
                self._fill_request_node(xml_node, sub_node)
        return xml_node

    @staticmethod
    def _hash_reference(signature_node, transformed_reference):
        """Формирует блок SignedInfo и вычисляет хеш от переданного референс."""
        signed_info = etree.SubElement(signature_node, f"{DS_PREFIX}SignedInfo")
        # Информация о блоке
        # Алгоритм каноникализации, который будет применен к блоку для формирования строки.
        # Эта строка будет использована для подписи
        etree.SubElement(
            signed_info, f"{DS_PREFIX}CanonicalizationMethod", Algorithm=C14N_TRANSFORM
        )
        # Алгоритм подписи, который будет применен к строке, сформированной по алгоритму выше.
        etree.SubElement(signed_info, f"{DS_PREFIX}SignatureMethod", Algorithm=SIGNATURE_METHOD)
        # Блок референса. Для гиис - структура с тэгом в основной части сообщения
        reference_node = etree.SubElement(
            signed_info, f"{DS_PREFIX}Reference", URI=f"#{REQUEST_DATA_TAG}"
        )
        # Применяемые трансформы над референсом (RequestData)
        transforms = etree.SubElement(reference_node, f"{DS_PREFIX}Transforms")
        # стандартный c14n трансформ
        etree.SubElement(transforms, f"{DS_PREFIX}Transform", Algorithm=C14N_TRANSFORM)
        # СМЕВ трансформ.
        etree.SubElement(transforms, f"{DS_PREFIX}Transform", Algorithm=SMEV_TRANSFORM)
        # Метод, который будет применятся для вычисления хещ-значения
        etree.SubElement(reference_node, f"{DS_PREFIX}DigestMethod", Algorithm=DIGEST_METHOD)
        # Считаем хеш
        hashedData = pycades.HashedData()
        hashedData.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
        hashedData.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
        hashedData.Hash(transformed_reference)
        # Вычесленный хеш нужно передать как base64 строку
        hash_value_b64 = base64.b64encode(bytearray.fromhex(hashedData.Value)).decode()
        digest_value = etree.SubElement(reference_node, f"{DS_PREFIX}DigestValue")
        digest_value.text = hash_value_b64
        return signed_info

    def _transform_node(self, xml_node, smev=False) -> str:
        """
        Выполняет трансформ c14n над переданной нодой. Дополнительно, можно сделать СМЕВ.
        Возвращает строку в формате base64, так как она используется для генерации хеша и подписи.
        """
        if smev:
            prev_c14n_bytes = etree.tostring(
                xml_node,
                method="c14n",
                exclusive=True,
                with_comments=False,
                inclusive_ns_prefixes=None,
            )
            gost_transformer = GOSTXMLTransform.from_bytes(prev_c14n_bytes)
            gost_transformer_bytes = gost_transformer.to_bytes()
            xml_node = etree.fromstring(gost_transformer_bytes)
        transformed = etree.tostring(
            xml_node, method="c14n", exclusive=True, with_comments=False, inclusive_ns_prefixes=None
        )
        return base64.b64encode(transformed).decode()

    @staticmethod
    def _sign_signed_info(signature_node, transformed_signed_info):
        """Выполняем подпись SignedInfo"""
        # Тут вообще жесть. Сначало считаем хеш от SignedINfo, а потом от него подпись.
        hashedData = pycades.HashedData()
        hashedData.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
        hashedData.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
        hashedData.Hash(transformed_signed_info)
        # Подпись
        signed_data = pycades.RawSignature()
        signature_hex: str = signed_data.SignHash(hashedData, CLIENT_CERT)
        # Переворачиваем значение, так как нужно получить число в формате BigEndian
        inverted_signature_bytes = bytearray(reversed(bytearray.fromhex(signature_hex)))
        signature_base64 = base64.b64encode(inverted_signature_bytes).decode("utf-8")
        # Помещаем подпись в документ
        signature_value_node = etree.SubElement(signature_node, f"{DS_PREFIX}SignatureValue")
        signature_value_node.text = signature_base64

    @staticmethod
    def _insert_key_info(signature_node):
        """Вставляем сертификат клиента"""
        key_info = etree.SubElement(signature_node, f"{DS_PREFIX}KeyInfo")
        x509_data = etree.SubElement(key_info, f"{DS_PREFIX}X509Data")
        cert_node = etree.SubElement(x509_data, f"{DS_PREFIX}X509Certificate")
        cert_node.text = CLIENT_CERT.Export(pycades.CADESCOM_ENCODE_BASE64)

    async def _send(self):
        """Отправляет запрос и возвращает разпарсенный документ"""
        client = self._get_soap_client()
        with client.settings(raw_response=True):
            response = await client.transport.post(
                address="http://0.0.0.0:1500/ws/v3/",
                message=self.to_string(),
                headers={"Content-Type": "text/xml; charset=utf-8"},
            )
        return etree.fromstring(response.content)

    async def send(self) -> tuple[str, str] | tuple[None, None]:
        """Парсим ответ. Реализцаия для методов группы Send."""
        root = await self._send()
        message_id = status = None
        message_id_result: list | None = root.xpath('//*[local-name()="messageId"]/text()')
        if message_id_result is not None:
            message_id = message_id_result[0]
        status_result: list | None = root.xpath('//*[local-name()="status"]/text()')
        if status_result is not None:
            status = status_result[0]
        return message_id, status
