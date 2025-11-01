from fastapi import APIRouter
from zeep import AsyncClient, Client
from zeep.transports import Transport
from lxml import etree
from zeep.helpers import serialize_object
import pycades
import re
from zeep import xsd


router = APIRouter(prefix="/try1")


TEMPLATE = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="urn://xsd.dmdk.goznak.ru/exchange/3.0">
<soapenv:Header/>
<soapenv:Body>
<ns:SendGetGlossaryRequest>
<ns:CallerSignature></ns:CallerSignature>
<ns:RequestData id="body">
<ns:type>GEMSTONE_COLOR_TYPE</ns:type>
<ns:page>1</ns:page>
<ns:size>25</ns:size>
</ns:RequestData>
</ns:SendGetGlossaryRequest>
</soapenv:Body>
</soapenv:Envelope>
"""

def test():
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert(certs.Count != 0), "Certificates with private key not found"

    signer = pycades.Signer()
    signer.Certificate = certs.Item(1)
    signer.CheckCertificate = True

    content_to_sign = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    content_to_sign += "<!-- "
    content_to_sign += "XML Security Library example: Original XML doc file for sign2 example. "
    content_to_sign += "-->"
    content_to_sign += "<Envelope xmlns=\"urn:envelope\">"
    content_to_sign += "  <Data>"
    content_to_sign += "    Hello, World!"
    content_to_sign += "  </Data>"
    content_to_sign += "  <Node xml:id=\"nodeID\">"
    content_to_sign += "    Hello, Node!"
    content_to_sign += "  </Node>" + " " + "</Envelope>"

    signedXML = pycades.SignedXML()
    signedXML.Content = content_to_sign
    signedXML.SignatureType = pycades.CADESCOM_XML_SIGNATURE_TYPE_ENVELOPED | pycades.CADESCOM_XADES_BES
    signature = signedXML.Sign(signer)

    print("--Signature--")
    print(signature)
    print("----")

    signedXML.Content = ""
    signedXML.Verify(signature)
    assert(signature == signedXML.Content), "Incorrect value of SignedXML.Verify result"
    print("Verified successfully")


def create_minimal_soap_template():
    """Создает SOAP с минимальным шаблоном подписи"""
    template = TEMPLATE
    template.replace('    ', '')

    signed_template = sign(template)
    with open('/app/logs/signed_template.xml', 'w') as file:
        file.write(signed_template)
    signed_root = etree.fromstring(signed_template.encode('utf-8'))
    signed_signature = signed_root.find('.//{http://www.w3.org/2000/09/xmldsig#}Signature')

    canonicalization_method = signed_signature.find('.//{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod')
    signature_method = signed_signature.find('.//{http://www.w3.org/2000/09/xmldsig#}SignatureMethod')
    digest_method = signed_signature.find('.//{http://www.w3.org/2000/09/xmldsig#}DigestMethod')
    digest_value = signed_signature.find('.//{http://www.w3.org/2000/09/xmldsig#}DigestValue')
    signature_value = signed_signature.find('.//{http://www.w3.org/2000/09/xmldsig#}SignatureValue')
    key_info = signed_signature.find('.//{http://www.w3.org/2000/09/xmldsig#}KeyInfo')

    template_root = etree.fromstring(template.encode('utf-8'))
    caller_signature = template_root.find('.//{urn://xsd.dmdk.goznak.ru/exchange/3.0}CallerSignature')
    signature_se = etree.SubElement(
        caller_signature,
        '{http://www.w3.org/2000/09/xmldsig#}Signature',
        nsmap={'ds': 'http://www.w3.org/2000/09/xmldsig#'}
    )
    signedinfo_se = etree.SubElement(
        signature_se,
        '{http://www.w3.org/2000/09/xmldsig#}SignedInfo'
    )
    signedinfo_se.append(canonicalization_method)
    signedinfo_se.append(signature_method)

    reference_se = etree.SubElement(
        signedinfo_se,
        '{http://www.w3.org/2000/09/xmldsig#}Reference',
        URI="#body"
    )
    transforms_se = etree.SubElement(
        reference_se,
        '{http://www.w3.org/2000/09/xmldsig#}Transforms',
    )
    transform_1_se = etree.SubElement(
        transforms_se,
        '{http://www.w3.org/2000/09/xmldsig#}Transform',
        Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"
    )
    transform_2_se = etree.SubElement(
        transforms_se,
        '{http://www.w3.org/2000/09/xmldsig#}Transform',
        Algorithm="urn://smev-gov-ru/xmldsig/transform"
    )
    reference_se.append(digest_method)
    reference_se.append(digest_value)
    signature_se.append(signature_value)
    signature_se.append(key_info)

    # caller_signature.append(signed)
    template_xml = etree.tostring(
        template_root, 
        encoding='utf-8',
        xml_declaration=False
    ).decode('utf-8')
    return template_xml


def sign(xml_doc: str):
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert(certs.Count != 0), "Certificates with private key not found"
    signer = pycades.Signer()
    signer.Certificate = certs.Item(1)
    signer.CheckCertificate = True

    signedXML = pycades.SignedXML()
    signedXML.Content = xml_doc
    signedXML.SignatureType = pycades.CADESCOM_XMLDSIG_TYPE
    signature = signedXML.Sign(signer)
    return signature


@router.get("/build_soap_message", status_code=200)
async def build_soap_message() -> list[str]:
    """Вручную собираем соап сообщение с подписью"""
    # Создаем клиент
    client = Client('./src/exchange3.wsdl')

    request_data_elem = create_minimal_soap_template()
    with open('/app/logs/request.xml', mode='w', encoding='utf-8') as file:
        file.write(etree.tostring(etree.fromstring(request_data_elem), pretty_print=True, encoding='unicode'))

    # Отправляем сообщение
    with client.settings(raw_response=True):
        response = client.transport.post(
            address='http://0.0.0.0:1500/ws/v3/',
            message=request_data_elem,
            headers={'Content-Type': 'text/xml; charset=utf-8'}
        )
    decoded = response.content.decode('utf-8')
    response = [str(response)]
    pp = etree.tostring(etree.fromstring(decoded), pretty_print=True, encoding='unicode')
    response.extend(pp.split('\n'))
    with open('/app/logs/response.xml', mode='w', encoding='utf-8') as file:
        file.writelines(pp)
    return response


@router.get("/do_request_with_signature", status_code=200)
async def do_some_request_with_sign() -> str:
    """Делает запрос с подписью"""
    client = AsyncClient(wsdl="./src/exchange3.wsdl")
    request_data = {
        'id': 'id',
        'type': 'GEMSTONE_COLOR_TYPE',
        'page': 1,
        'size': 50
    }
    request_data_str = dict_to_xml_clean(request_data)
    signed = sign(request_data_str)
    print(signed)
    # signature_xml = decoded_bytes.decode('utf-8')
    signature_value = re.findall(r'<ds:SignatureValue[^>]*>(.*?)</ds:SignatureValue>', signed, re.DOTALL | re.IGNORECASE)[0]
    response = await client.service.SendGetGlossary(
        CallerSignature=xsd.AnyObject(xsd.String(), signed),
        OGRN="1234567890123",
        IDTOP="TOP123456789",
        RequestData=request_data
    )
    message_id = response.ResponseData.messageId
    return message_id
    response = await client.service.CheckGetGlossary(
        OGRN="1234567890123",
        IDTOP="TOP123456789",
        RequestData={'id': 'id', 'messageId': message_id}
    )
    return serialize_object(response.ResponseData)  # type: ignore


def dict_to_xml_clean(request_data, namespace_uri='http://dmdk.gov.ru/ns', prefix='ns'):
    """
    Создает чистый XML с префиксами но без xmlns объявлений
    """
    # Создаем временный корневой элемент
    NSMAP = {prefix: namespace_uri}
    intermediary = etree.Element("TemporaryRoot", nsmap=NSMAP)
    # Создаем RequestData
    request_data_elem = etree.SubElement(intermediary, f"{{{namespace_uri}}}RequestData")
    if 'id' in request_data:
        request_data_elem.set("id", str(request_data['id']))
    for key, value in request_data.items():
        if key != 'id':
            child = etree.SubElement(request_data_elem, f"{{{namespace_uri}}}{key}")
            child.text = str(value)
    # Извлекаем RequestData и вручную создаем новый элемент без неймспейсов
    clean_root = etree.Element("RequestData")
    # Копируем атрибуты (кроме xmlns)
    for name, value in request_data_elem.attrib.items():
        if not name.startswith('xmlns'):
            clean_root.set(name, value)
    # Копируем дочерние элементы, преобразуя имена
    for child in request_data_elem:
        tag_name = child.tag.split('}')[-1]  # Убираем неймспейс из тега
        new_child = etree.SubElement(clean_root, tag_name)
        new_child.text = child.text
    return etree.tostring(clean_root, encoding='unicode', pretty_print=True)


@router.get('/health_from_string', status_code=200)
async def do_health_request() -> list:
    """Пример запроса к health из строки"""
    soap_request_str = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="urn://xsd.dmdk.goznak.ru/exchange/3.0">
    <soapenv:Header/>
    <soapenv:Body>
        <ns:HealthRequest>
            <ns:TestMessage>Test</ns:TestMessage>
            <ns:RequestData id="id">
                <ns:DataForTest>Test</ns:DataForTest>
            </ns:RequestData>
        </ns:HealthRequest>
    </soapenv:Body>
    </soapenv:Envelope>'''
    envelope = etree.fromstring(soap_request_str.encode('utf-8'))
    transport = Transport()
    url = "http://0.0.0.0:1500/ws/v3/"
    response = transport.post_xml(
        address=url,
        envelope=envelope,
        headers={
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '"Health"'
        }
    )
    return etree.tostring(etree.fromstring(response.content), pretty_print=True, encoding='unicode').split('\n')


@router.get('/health_compiled', status_code=200)
async def do_health_request1() -> str:
    """Сборный запрос к Health. 
    На проде будем использовать асинхронный клиент и править а править wsdl будем перед приемом вручную.
    Если все удачно, вернет значение Running.
    """
    client = Client(wsdl="http://0.0.0.0:1500/ws/v3/exchange3.wsdl")
    binding_name = r'{urn://xsd.dmdk.goznak.ru/exchange/3.0}exchangeSoap11'
    new_endpoint = 'http://0.0.0.0:1500/ws/v3'
    service = client.create_service(binding_name, new_endpoint)
    health_request_data = {
        'DataForTest': 'Hello from my system!',
        'id': 'req-12345-abcde'
    }
    response = service.Health(
        TestMessage="test",
        OGRN="1234567890123",
        IDTOP="TOP123456789",
        agent="MyPythonApp v1.0",
        RequestData=health_request_data
    )
    return response.ResponseData.Result


@router.get('/health_compiled_async', status_code=200)
async def do_health_request2() -> str:
    """Делает запрос при помощи асинхронного клиента, с передачей exchange напрямую"""
    client = AsyncClient(wsdl="./src/exchange3.wsdl")
    health_request_data = {
        'DataForTest': 'Hello from my system!',
        'id': 'req-12345-abcde'
    }
    response = await client.service.Health(
        TestMessage="test",
        OGRN="1234567890123",
        IDTOP="TOP123456789",
        agent="MyPythonApp v1.0",
        RequestData=health_request_data
    )
    return response.ResponseData.Result
