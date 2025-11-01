from fastapi import APIRouter
import pycades
from lxml import etree
from src.xml_schemas.gost_xml_transform.gost_xml_transform import GOSTXMLTransform
import base64
from zeep import Client


class Signer:
    """Класс для подписи xml-документов собранных на основе lxml.etree."""

    # Инициируем pycades Store - хранилище сертификатов
    STORE = pycades.Store()
    STORE.Open(
        pycades.CADESCOM_CONTAINER_STORE, 
        pycades.CAPICOM_MY_STORE, 
        pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED
    )
    # Открываем Сертификаты
    CERTS = STORE.Certificates
    assert CERTS.Count != 0, "Certificates with private key not found"
    # Объект pycades для подписи
    CERT = CERTS.Item(1)
    SIGNER = pycades.Signer()
    SIGNER.Certificate = CERT
    SIGNER.CheckCertificate = True

    def __init__(self) -> None:
        pass


router = APIRouter(prefix="/try4")


@router.get('/build_message', status_code=200)
async def build_message() -> list[str]:
    """Тестим, тестим"""
    template = build_template()
    digest_value = sign_ref_element(template)
    insert_digest_value(template, digest_value)
    sign_signed_info(template)
    insert_key_info(template)

    template.getroottree().write(
        '/app/logs/request.xml', 
        encoding="utf-8", 
        xml_declaration=True,
        pretty_print=True
    )

    with open('/app/logs/request.xml', encoding='utf-8') as file:
        template_str = file.read()

    client = Client('./src/exchange3.wsdl')

    # Получить endpoint из WSDL
    service = client.wsdl
    print(dir(service))
    print(service.services)
    # port = service.ports[0]
    # endpoint_from_wsdl = port.binding_options['address']

    with client.settings(raw_response=True):
        response = client.transport.post(
            address='http://0.0.0.0:1500/ws/v3/',
            message=template_str,
            headers={'Content-Type': 'text/xml; charset=utf-8'}
        )

    decoded = response.content.decode('utf-8')
    response = [str(response)]
    pp = etree.tostring(etree.fromstring(decoded), pretty_print=True, encoding='unicode')
    
    with open('/app/logs/response.xml', mode='w', encoding='utf-8') as file:
        file.writelines(pp)

    response.extend(pp.split('\n'))
    return response


NSMAP = {
    'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
    'ns1': 'urn://xsd.dmdk.goznak.ru/exchange/3.0'
}
DSMAP = {'ds': "http://www.w3.org/2000/09/xmldsig#"}


def build_template():
    root = etree.Element(f'{{{NSMAP["soapenv"]}}}Envelope', nsmap=NSMAP)
    header = etree.SubElement(root, f'{{{NSMAP["soapenv"]}}}Header')
    body = etree.SubElement(root, f'{{{NSMAP["soapenv"]}}}Body')

    request = etree.SubElement(body, f'{{{NSMAP["ns1"]}}}SendGetGlossaryRequest')
    caller_signature = etree.SubElement(request, f'{{{NSMAP["ns1"]}}}CallerSignature')

    request_data = etree.SubElement(request, f'{{{NSMAP["ns1"]}}}RequestData', id='body')
    _type = etree.SubElement(request_data, f'{{{NSMAP["ns1"]}}}type')
    _type.text = 'GEMSTONE_COLOR_TYPE'
    page = etree.SubElement(request_data, f'{{{NSMAP["ns1"]}}}page')
    page.text = '1'
    size = etree.SubElement(request_data, f'{{{NSMAP["ns1"]}}}size')
    size.text = '25'

    return root


def sign_ref_element(template):
    """Возвращает digest_value"""
    ref_element = template.find(f'.//{{{NSMAP["ns1"]}}}RequestData')

    c14n_bytes = etree.tostring(
        ref_element,
        method="c14n",
        exclusive=True,
        with_comments=False,
        inclusive_ns_prefixes=None,
    )

    transformer = GOSTXMLTransform.from_bytes(c14n_bytes)
    transformed_bytes = transformer.to_bytes()
    b64_transformed_bytes = base64.b64encode(transformed_bytes).decode()

    hashedData = pycades.HashedData()
    hashedData.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashedData.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashedData.Hash(b64_transformed_bytes)

    return base64.b64encode(bytearray.fromhex(hashedData.Value)).decode()


def insert_digest_value(template, digest_value):
    caller_signature = template.find(f'.//{{{NSMAP["ns1"]}}}CallerSignature')
    signature = etree.SubElement(caller_signature, f'{{{DSMAP["ds"]}}}Signature', nsmap=DSMAP)

    signed_info = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}SignedInfo')

    etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}CanonicalizationMethod', Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}SignatureMethod', Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34102012-gostr34112012-256")

    reference = etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}Reference', URI="#body")

    transforms = etree.SubElement(reference, f'{{{DSMAP["ds"]}}}Transforms')
    etree.SubElement(transforms, f'{{{DSMAP["ds"]}}}Transform', Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    etree.SubElement(transforms, f'{{{DSMAP["ds"]}}}Transform', Algorithm="urn://smev-gov-ru/xmldsig/transform")

    etree.SubElement(reference, f'{{{DSMAP["ds"]}}}DigestMethod', Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-256")
    digest_value_el = etree.SubElement(reference, f'{{{DSMAP["ds"]}}}DigestValue')

    digest_value_el.text = digest_value


def sign_signed_info(template):
    signed_info_node = template.find(f'.//{{{DSMAP["ds"]}}}SignedInfo')
    c14n_signed_info = etree.tostring(
        signed_info_node,
        method="c14n",
        exclusive=True,
        with_comments=False
    )
    signedData = pycades.SignedData()
    signedData.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    signedData.Content = base64.b64encode(c14n_signed_info).decode()
    signature = signedData.SignCades(Signer.SIGNER, pycades.CADESCOM_CADES_BES, True)
    signatureValue =  base64.b64encode(base64.b64decode(signature)).decode()
    signature_node = template.find(f'.//{{{DSMAP["ds"]}}}Signature')
    signature_value_node = etree.SubElement(signature_node, f'{{{DSMAP["ds"]}}}SignatureValue')
    signature_value_node.text = signatureValue


def insert_key_info(request):
    signature = request.find(f'.//{{{DSMAP["ds"]}}}Signature')
    key_info = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}KeyInfo')
    x509_data = etree.SubElement(key_info, f'{{{DSMAP["ds"]}}}X509Data')
    x509_certificate = etree.SubElement(x509_data, f'{{{DSMAP["ds"]}}}X509Certificate')
    x509_certificate.text = Signer.CERT.Export(pycades.CADESCOM_ENCODE_BASE64)
