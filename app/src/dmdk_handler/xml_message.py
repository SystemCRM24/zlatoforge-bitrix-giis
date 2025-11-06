from lxml import etree  # type:ignore

from .cypher import dmdk_hash, dmdk_signature, get_certificate
from .gost_xml_transform.gost_xml_transform import GOSTXMLTransform
from .node import Node


class SignedXMLMessage:
    """Собирает подписанное XML-сообщение для ДМДК."""

    __slots__ = ("endpoint", "request_data", "_root")

    NSMAP = {
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "ns": "urn://xsd.dmdk.goznak.ru/exchange/3.0",
    }
    SOAPENV_PREFIX = f"{{{NSMAP['soapenv']}}}"
    NS_PREFIX = f"{{{NSMAP['ns']}}}"
    DSMAP = {"ds": "http://www.w3.org/2000/09/xmldsig#"}  # Специфичный неймспейс нужный для подписи
    DS_PREFIX = f"{{{DSMAP['ds']}}}"
    C14N_TRANSFORM = "http://www.w3.org/2001/10/xml-exc-c14n#"
    SMEV_TRANSFORM = "urn://smev-gov-ru/xmldsig/transform"
    SIGNATURE_METHOD = "urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34102012-gostr34112012-256"
    DIGEST_METHOD = "urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-256"
    REQUEST_DATA_TAG = "RequestData"

    def __init__(self, endpoint: str, request_data: Node) -> None:
        self.endpoint = endpoint
        self.request_data = request_data
        self._root = None

    def to_bytes(self, pretty_print=False) -> bytes:
        """Возвращает собранное сообщение в байтовом представлении"""
        if self._root is None:
            raise ValueError("Message is not builded. Use build_message method first.")
        return etree.tostring(self._root, pretty_print=pretty_print)

    def to_string(self, encoding="utf-8", pretty_print=False) -> str:
        """Возвращает собранное сообщение в строковом представлении"""
        return self.to_bytes(pretty_print).decode(encoding=encoding)

    def build(self):
        """Собирает и подписывает сообщение"""
        if self._root is not None:
            return
        self._normalize_request_data()
        local_nsmap = self._get_local_nsmap()
        # Собираем корневую структуру
        root_node = self._root = etree.Element(f"{self.SOAPENV_PREFIX}Envelope", nsmap=local_nsmap)
        etree.SubElement(root_node, f"{self.SOAPENV_PREFIX}Header")
        body_node = etree.SubElement(root_node, f"{self.SOAPENV_PREFIX}Body")
        request_node = etree.SubElement(body_node, f"{self.NS_PREFIX}{self.endpoint}Request")
        caller_signature_node = etree.SubElement(request_node, f"{self.NS_PREFIX}CallerSignature")
        # Заполняем данные для запроса
        request_data_node = self._fill_request_node(request_node, self.request_data)
        signature_node = etree.SubElement(
            caller_signature_node, f"{self.DS_PREFIX}Signature", nsmap=self.DSMAP
        )
        transformed_reference = self._transform_node(request_data_node, smev=True)
        signed_info_node = self._create_and_fill_signed_info(signature_node, transformed_reference)
        transformed_signed_info = self._transform_node(signed_info_node)
        self._sign_signed_info(signature_node, transformed_signed_info)
        self._insert_key_info(signature_node)

    def _normalize_request_data(self):
        """Нормализует корневую ноду"""
        self.request_data.name = self.REQUEST_DATA_TAG
        self.request_data.namespace = self.NSMAP["ns"]
        self.request_data.kwargs["id"] = self.REQUEST_DATA_TAG

    def _get_local_nsmap(self) -> dict[str, str]:
        """Возвращает карту пространства имен для этого сообщения."""

        def find_namespaces(node: Node, accumulator: set):
            """Рекурсивно обходит node для сбора существующиъ пространств имен"""
            accumulator.add(node.namespace)
            if not isinstance(node._value, str):
                for sub_node in node._value:
                    find_namespaces(sub_node, accumulator)  # type:ignore

        accumulator = set()
        find_namespaces(self.request_data, accumulator)
        local_nsmap = self.NSMAP.copy()
        for i, v in enumerate(accumulator, start=1):
            local_nsmap[f"ns{i}"] = v
        return local_nsmap

    def _fill_request_node(self, parent_xml_node, node: Node):
        """Рекурсивно заполняет parent_node значениями из node."""
        xml_node = etree.SubElement(
            parent_xml_node, f"{{{node.namespace}}}{node.name}", **node.kwargs
        )
        if isinstance(node._value, str):
            xml_node.text = node._value
        else:
            for sub_node in node._value:
                self._fill_request_node(xml_node, sub_node)
        return xml_node

    def _transform_node(self, xml_node, smev=False) -> bytes:
        """Выполняет трансформ c14n над переданной нодой. Дополнительно, можно сделать СМЕВ."""
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
        return transformed

    def _create_and_fill_signed_info(self, signature_node, transformed_reference: bytes):
        """Формирует блок SignedInfo и вычисляет хеш от переданного референс."""
        signed_info = etree.SubElement(signature_node, f"{self.DS_PREFIX}SignedInfo")
        # Информация о блоке
        # Алгоритм каноникализации, который будет применен к блоку для формирования строки.
        # Эта строка будет использована для подписи
        etree.SubElement(
            signed_info, f"{self.DS_PREFIX}CanonicalizationMethod", Algorithm=self.C14N_TRANSFORM
        )
        # Алгоритм подписи, который будет применен к строке, сформированной по алгоритму выше.
        etree.SubElement(
            signed_info, f"{self.DS_PREFIX}SignatureMethod", Algorithm=self.SIGNATURE_METHOD
        )
        # Блок референса. Для гиис - структура с тэгом в основной части сообщения
        reference_node = etree.SubElement(
            signed_info, f"{self.DS_PREFIX}Reference", URI=f"#{self.REQUEST_DATA_TAG}"
        )
        # Применяемые трансформы над референсом (RequestData)
        transforms = etree.SubElement(reference_node, f"{self.DS_PREFIX}Transforms")
        # стандартный c14n трансформ
        etree.SubElement(transforms, f"{self.DS_PREFIX}Transform", Algorithm=self.C14N_TRANSFORM)
        # СМЕВ трансформ.
        etree.SubElement(transforms, f"{self.DS_PREFIX}Transform", Algorithm=self.SMEV_TRANSFORM)
        # Метод, который будет применятся для вычисления хещ-значения
        etree.SubElement(
            reference_node, f"{self.DS_PREFIX}DigestMethod", Algorithm=self.DIGEST_METHOD
        )
        # Считаем хеш
        digest_value = etree.SubElement(reference_node, f"{self.DS_PREFIX}DigestValue")
        digest_value.text = dmdk_hash(transformed_reference)
        return signed_info

    def _sign_signed_info(self, signature_node, transformed_signed_info: bytes):
        """Выполняем подпись SignedInfo"""
        signature_value_node = etree.SubElement(signature_node, f"{self.DS_PREFIX}SignatureValue")
        signature_value_node.text = dmdk_signature(transformed_signed_info)

    def _insert_key_info(self, signature_node):
        """Вставляем сертификат клиента"""
        key_info = etree.SubElement(signature_node, f"{self.DS_PREFIX}KeyInfo")
        x509_data = etree.SubElement(key_info, f"{self.DS_PREFIX}X509Data")
        cert_node = etree.SubElement(x509_data, f"{self.DS_PREFIX}X509Certificate")
        cert_node.text = get_certificate()
