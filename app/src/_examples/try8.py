from fastapi import APIRouter
from typing import Self
from lxml import etree
import pycades
import base64
from src.xml_handlers.base.gost_xml_transform.gost_xml_transform import GOSTXMLTransform
from zeep import Client


class XMLTemplate:
    """Шаблон xml-документа для ГИИС"""
    NSMAP = {
        'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/', 
        'ns': 'urn://xsd.dmdk.goznak.ru/exchange/3.0'
    }

    @classmethod
    def from_dict(cls, request_data: dict) -> Self:
        """Собираем сообщение из вложенного словаря по соглашению:
        Так как, RequestData уже включен в шаблон, то request_data должна содержать вложенные
        сущности. Для каждого метода они свои и описаны в документации.
        - Ключ request_data (или вложенного словаря) - имя тэга в xml документе.
        - значение - словарь, с обязательными ключами ns и value.
        --- ns - указание пространства имен для тэга
        --- value - значение этого тэга. Могут быть 2 типа значений. 1 - примитивный тип (строка
        число) 2 - словарь. Если значение словарь, то это будет расценено как очередной тэг xml 
        документа, который в свою очередь также должен быть оформлен по правилам.
        --- в словарь для тэга можно добавить и другие ключи: значения. Они будут прикреплены
        как атрибуты к соответствующему тэгу.
        - Пример request_data для запроса SendGetGlossaryRequest:
        {
            'type': {'ns': 'ns', 'value': 'GEMSTONE_COLOR_TYPE'},
            'page': {'ns': 'ns', 'value': 1},
            'size': {'ns': 'ns', 'value': 25}
        }
        """
        xml_doc = cls(request_data)
        xml_doc.build_message()
        return xml_doc

    def __init__(self, request_data: dict) -> None:
        self.request_data = request_data
        self.request_data_tag = 'RequestData'
        self._root_node = None
        self._request_data_node = None
        self._caller_signature_node = None

    def to_bytes(self, pretty_print=False) -> bytes:
        """Возвращает собранное сообщение в байтовом представлении"""
        if self._root_node is None:
            raise ValueError('Message is not builded. Use build_message method first.')
        return etree.tostring(self._root_node, pretty_print=pretty_print)
    
    def to_string(self, encoding='utf-8', pretty_print=False) -> str:
        """Возвращает собранное сообщение в строковом представлении"""
        return self.to_bytes(pretty_print).decode(encoding=encoding)

    def build_message(self):
        """
        Полностью собирает сообщение, в том числе с подписью.
        Для прода (отправки сообщений в гиис дмдк) параметр pretty_print должен быть False.
        """
        self._create_root_node()
        self._fill_request_node(self._request_data_node, self.request_data)
    
    def _create_root_node(self):
        """Собирает основные корневые узлы xml-сообщения."""
        soapenv_prefix = f'{{{self.NSMAP["soapenv"]}}}'
        ns_prefix = f'{{{self.NSMAP['ns']}}}'
        # Собираем корневую структуру
        root = self._root_node = etree.Element(f'{soapenv_prefix}Envelope', nsmap=self.NSMAP)
        etree.SubElement(root, f'{soapenv_prefix}Header')
        body = etree.SubElement(root, f'{soapenv_prefix}Body')
        # Наполняем тело сообщения
        request = etree.SubElement(body, f'{ns_prefix}{self.__class__.__name__}')
        self._caller_signature_node = etree.SubElement(request, f'{ns_prefix}Signature')
        self._request_data_node = etree.SubElement(request, f'{ns_prefix}RequestData', id=self.request_data_tag)
    
    def _fill_request_node(self, parent_node, request_data: dict[str, dict]):
        """Рекурсивно заполняет parent_node значениями из request_data."""
        for node_name, node_params in request_data.items():
            ns = node_value = None
            kwargs = {}
            for key, value in node_params.items():
                match key:
                    case 'ns':
                        ns = value
                    case 'value':
                        node_value = value
                    case _:
                        kwargs[key] = value
            if ns is None or node_value is None:
                raise ValueError(f'Namespace or value in node {node_name} not defined.')
            node = etree.SubElement(parent_node, f'{{{self.NSMAP[ns]}}}{node_name}', **kwargs)
            if isinstance(node_value, dict):
                self._fill_request_node(node, node_value)
            else:
                node.text = str(node_value)


class SignedXMLTemplate(XMLTemplate):
    """Расширение шаблона для ГИИС. Реализует механизмы подписи"""

    # Пространство имен ds необходимо для ветки с подписью
    DSMAP = {'ds': "http://www.w3.org/2000/09/xmldsig#"}
    # Инициируем pycades
    STORE = pycades.Store()
    STORE.Open(
        pycades.CADESCOM_CONTAINER_STORE, 
        pycades.CAPICOM_MY_STORE, 
        pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED
    )
    CERTS = STORE.Certificates
    assert CERTS.Count != 0, "Certificates with private key not found"
    # Объект pycades для подписи
    CERT = CERTS.Item(1)
    SIGNER = pycades.Signer()
    SIGNER.Certificate = CERT
    SIGNER.CheckCertificate = True

    def __init__(self, request_data: dict) -> None:
        super().__init__(request_data)
        self._digest_value_node = None
        self._signature_value_node = None
        self._cert_node = None
    
    def build_message(self):
        super().build_message()
        self._create_signature_node()
        self._sign_reference()

    def _create_signature_node(self):
        """Собирает ветку CallerSignature"""
        ds_prefix = f'{{{self.DSMAP['ds']}}}'
        # signature = etree.SubElement(self._caller_signature_node, f'{ds_prefix}Signature', nsmap=self.DSMAP)
        signature = self._caller_signature_node
        # Информация о подписи
        signed_info = etree.SubElement(signature, f'{ds_prefix}SignedInfo')
        etree.SubElement(signed_info, f'{ds_prefix}CanonicalizationMethod', Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
        etree.SubElement(signed_info, f'{ds_prefix}SignatureMethod', Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34102012-gostr34112012-256")
        # Референс
        reference = etree.SubElement(signed_info, f'{ds_prefix}Reference', URI=f"#{self.request_data_tag}")
        # Применяемые трансформы над референсом (RequestData)
        transforms = etree.SubElement(reference, f'{ds_prefix}Transforms')
        etree.SubElement(transforms, f'{ds_prefix}Transform', Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
        # etree.SubElement(transforms, f'{ds_prefix}Transform', Algorithm="urn://smev-gov-ru/xmldsig/transform")
        # Метод и значение хеш-суммы вычисленное от референса
        etree.SubElement(reference, f'{ds_prefix}DigestMethod', Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-256")
        self._digest_value_node = etree.SubElement(reference, f'{ds_prefix}DigestValue')
        # self._digest_value_node.text = ""
        # Значение подписи.
        self._signature_value_node = etree.SubElement(signature, f'{ds_prefix}SignatureValue')
        # self._signature_value_node.text = ""
        # Ветка для ключа
        key_info = etree.SubElement(signature, f'{ds_prefix}KeyInfo')
        # x509_data = etree.SubElement(key_info, f'{ds_prefix}X509Data')
        # self._cert_node = etree.SubElement(x509_data, f'{ds_prefix}X509Certificate')
        # Сразу помещаем данные сертификата в сообщение
        # self._cert_node.text = self.CERT.Export(pycades.CADESCOM_ENCODE_BASE64)
    
    def _sign_reference(self):
        """Подписываем референс"""
        transformed_reference = self._transform_reference()
        print(transformed_reference)
        # Считаем хеш
        signedData = pycades.SignedData()
        # signedData.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
        # signedData.Content = base64.b64encode(transformed_reference).decode()
        # signature = signedData.SignCades(self.SIGNER, pycades.CADESCOM_XMLDSIG_TYPE, True)
        # data_signature_b64 = base64.b64encode(base64.b64decode(signature)).decode()
        signedXML = pycades.SignedXML()
        signedXML.Content = transformed_reference
        signedXML.DigestMethod = pycades.XmlDsigGost3411Url2012256
        signedXML.SignatureMethod = pycades.XmlDsigGost3410Url2012256
        signed = signedXML.Sign(self.SIGNER)
        print(signed)
        # print(signed)        

    
    def _transform_reference(self) -> bytes:
        """Трансформ референса. Сначало смэв, потом с14n."""
        prev_c14n_bytes = etree.tostring(
            self._request_data_node,
            method="c14n",
            exclusive=True,
            with_comments=False,
            inclusive_ns_prefixes=None,
        )
        gost_transformer = GOSTXMLTransform.from_bytes(prev_c14n_bytes)
        gost_transformer_bytes = gost_transformer.to_bytes()
        gost_node = etree.fromstring(gost_transformer_bytes)
        return etree.tostring(
            gost_node, 
            method="c14n", 
            exclusive=True, 
            with_comments=False, 
            inclusive_ns_prefixes=None
        ).decode()


class SendGetGlossaryRequest(SignedXMLTemplate):
    """Используется для получения элементов справочника."""


router = APIRouter(prefix='/try8')


@router.get("/build_message")
async def build_message() -> list[str]:
    request_data = {
        'type': {'ns': 'ns', 'value': 'GEMSTONE_COLOR_TYPE'},
        'page': {'ns': 'ns', 'value': 1},
        'size': {'ns': 'ns', 'value': 25}
    }
    message = SendGetGlossaryRequest.from_dict(request_data)
    with open('/app/logs/request.xml', mode='wb') as file:
        file.write(message.to_bytes(True))

    client = Client('./src/exchange3.wsdl')
    with client.settings(raw_response=True):
        response = client.transport.post(
            address='http://0.0.0.0:1500/ws/v3/',
            message=message.to_string(),
            headers={'Content-Type': 'text/xml; charset=utf-8'}
        )
    decoded = response.content.decode('utf-8')
    response = [str(response)]
    pp = etree.tostring(etree.fromstring(decoded), pretty_print=True, encoding='unicode')
    with open('/app/logs/response.xml', mode='w', encoding='utf-8') as file:
        file.writelines(pp)
    response.extend(pp.split('\n'))
    return response
