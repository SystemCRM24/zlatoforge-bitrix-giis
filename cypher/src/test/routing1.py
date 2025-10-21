from fastapi import APIRouter
from lxml import etree
from zeep import Client
import pycades
import base64


router = APIRouter(prefix="/test", tags=['test1'])


NSMAP = {
    'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
    'ns': 'urn://xsd.dmdk.goznak.ru/exchange/3.0'
}
DSMAP = {'ds': "http://www.w3.org/2000/09/xmldsig#"}


@router.get('/build_message', status_code=200)
async def build_message() -> list[str]:
    template = build_template()
    insert_sign(template)

    with open('/app/logs/request.xml', mode='wb') as file:
        file.write(etree.tostring(template, pretty_print=True, encoding='utf-8'))

    template_str = etree.tostring(template, encoding='utf-8')
    client = Client('./src/exchange3.wsdl')
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


def build_template():
    root = etree.Element(f'{{{NSMAP["soapenv"]}}}Envelope', nsmap=NSMAP)
    header = etree.SubElement(root, f'{{{NSMAP["soapenv"]}}}Header')
    body = etree.SubElement(root, f'{{{NSMAP["soapenv"]}}}Body')

    request = etree.SubElement(body, f'{{{NSMAP["ns"]}}}SendGetGlossaryRequest')
    caller_signature = etree.SubElement(request, f'{{{NSMAP["ns"]}}}CallerSignature')

    request_data = etree.SubElement(request, f'{{{NSMAP["ns"]}}}RequestData', id='body')
    _type = etree.SubElement(request_data, f'{{{NSMAP["ns"]}}}type')
    _type.text = 'GEMSTONE_COLOR_TYPE'
    page = etree.SubElement(request_data, f'{{{NSMAP["ns"]}}}page')
    page.text = '1'
    size = etree.SubElement(request_data, f'{{{NSMAP["ns"]}}}size')
    size.text = '25'

    return root


def insert_sign(template):
    request_data = template.find(f'.//{{{NSMAP["ns"]}}}RequestData')

    data = etree.tostring(
        request_data, 
        method='c14n',
        exclusive=True,
        with_comments=False
    )
    data_to_sign = base64.b64encode(data).decode('utf-8')

    insert_hash_and_signature(template, data_to_sign)
    insert_key_info(template, data_to_sign)
    insert_certificate_info(template)


def insert_hash_and_signature(request, data_to_sign):
    caller_signature = request.find(f'.//{{{NSMAP["ns"]}}}CallerSignature')
    signature = etree.SubElement(caller_signature, f'{{{DSMAP["ds"]}}}Signature', nsmap=DSMAP)

    signed_info = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}SignedInfo')

    etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}CanonicalizationMethod', Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}SignatureMethod', Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34102012-gostr34112012-256")

    reference = etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}Reference', URI="#body")

    transforms = etree.SubElement(reference, f'{{{DSMAP["ds"]}}}Transforms')
    etree.SubElement(transforms, f'{{{DSMAP["ds"]}}}Transform', Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    etree.SubElement(transforms, f'{{{DSMAP["ds"]}}}Transform', Algorithm="urn://smev-gov-ru/xmldsig/transform")

    etree.SubElement(reference, f'{{{DSMAP["ds"]}}}DigestMethod', Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-256")
    digest_value = etree.SubElement(reference, f'{{{DSMAP["ds"]}}}DigestValue')

    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert(certs.Count != 0), "Certificates with private key not found"
    signer = pycades.Signer()
    signer.Certificate = certs.Item(1)
    signer.CheckCertificate = True

    hashed_data = pycades.HashedData()
    hashed_data.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashed_data.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashed_data.Hash(data_to_sign)

    hash_bytes = bytes.fromhex(hashed_data.Value)
    hash_base64 = base64.b64encode(hash_bytes).decode('utf-8')
    digest_value.text = hash_base64

    signed_data = pycades.SignedData()
    data_signature = signed_data.SignHash(hashed_data, signer, pycades.CADESCOM_CADES_BES, True)
    data_signature = base64.b64encode(data_signature).decode('utf-8')
 
    signature_value = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}SignatureValue')
    signature_value.text = data_signature


def insert_key_info(request, data_to_sign):
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert(certs.Count != 0), "Certificates with private key not found"
    signer = pycades.Signer()
    signer.Certificate = certs.Item(1)
    signer.CheckCertificate = True

    hashed_data = pycades.HashedData()
    hashed_data.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashed_data.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashed_data.Hash(data_to_sign)

    signed_data = pycades.SignedData()
    data_signature = signed_data.SignHash(hashed_data, signer, pycades.CADESCOM_CADES_BES, True)
    data_signature = base64.b64encode(data_signature).decode('utf-8')
 
    signature = request.find(f'.//{{{DSMAP["ds"]}}}Signature')
    signature_value = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}SignatureValue')
    signature_value.text = data_signature


def insert_certificate_info(request):
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certificates = store.Certificates
    cert = certificates.Item(1)

    signature = request.find(f'.//{{{DSMAP["ds"]}}}Signature')
    key_info = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}KeyInfo')
    x509_data = etree.SubElement(key_info, f'{{{DSMAP["ds"]}}}X509Data')
    x509_certificate = etree.SubElement(x509_data, f'{{{DSMAP["ds"]}}}X509Certificate')
    x509_certificate.text = cert.Export(pycades.CAPICOM_ENCODE_BASE64)
