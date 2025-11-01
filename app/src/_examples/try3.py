from fastapi import APIRouter
from lxml import etree
from zeep import Client
import pycades
import base64


router = APIRouter(prefix="/try3")


@router.get('/build_message_ai', status_code=200)
async def build_message() -> list[str]:
    check_embedded_license()

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


NSMAP = {
    'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
    'ns': 'urn://xsd.dmdk.goznak.ru/exchange/3.0'
}
DSMAP = {'ds': "http://www.w3.org/2000/09/xmldsig#"}


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
    request_data = template.find(f'.//{{{NSMAP["ns"]}}}RequestData[@id="body"]') 
    # 1. Применяем первое преобразование: Exclusive C14N
    data_after_c14n = etree.tostring(
        request_data, 
        method='c14n',
        exclusive=True,
        with_comments=False
    )
    # 2. Применяем второе преобразование: СМЭВ трансформация
    data_after_smev = apply_smev_transform(data_after_c14n)
    # Вычисляем хеш от данных после ВСЕХ преобразований
    data_to_sign = base64.b64encode(data_after_smev).decode('utf-8') 
    insert_hash_and_signature(template, data_to_sign)


def apply_smev_transform(xml_data):
    """
    Применяет преобразование urn://smev-gov-ru/xmldsig/transform
    Это специфичное преобразование СМЭВ для нормализации XML
    """
    try:
        # Парсим XML после C14N
        root = etree.fromstring(xml_data)
        # СМЭВ преобразование обычно включает:
        # - Дополнительную нормализацию пробелов
        # - Удаление лишних пробелов в текстовых узлах
        # - Нормализацию атрибутов
        for elem in root.iter():
            # Нормализация текстового содержимого
            if elem.text is not None:
                # Сохраняем значимые пробелы, но убираем лишние
                elem.text = ' '.join(elem.text.split())
            
            # Нормализация хвостового текста
            if elem.tail is not None:
                elem.tail = ' '.join(elem.tail.split())
        # Сериализуем обратно в канонической форме
        result = etree.tostring(
            root, 
            method='c14n',
            exclusive=True,
            with_comments=False
        )
        return result
    except Exception as e:
        # Если не получается применить СМЭВ трансформацию, 
        # возвращаем исходные данные (C14N)
        print(f"Warning: SMEV transform failed: {e}")
        return xml_data


def insert_hash_and_signature(template, data_to_sign):
    caller_signature = template.find(f'.//{{{NSMAP["ns"]}}}CallerSignature')
    signature = etree.SubElement(caller_signature, f'{{{DSMAP["ds"]}}}Signature', nsmap=DSMAP)

    signed_info = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}SignedInfo')

    # CanonicalizationMethod
    etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}CanonicalizationMethod', 
                    Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    
    # SignatureMethod
    etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}SignatureMethod', 
                    Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34102012-gostr34112012-256")
    # Reference
    reference = etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}Reference', URI="#body")
    transforms = etree.SubElement(reference, f'{{{DSMAP["ds"]}}}Transforms')
    
    # Transform 1: Exclusive C14'
    etree.SubElement(transforms, f'{{{DSMAP["ds"]}}}Transform', Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    # Transform 2: SMEV
    etree.SubElement(transforms, f'{{{DSMAP["ds"]}}}Transform', Algorithm="urn://smev-gov-ru/xmldsig/transform")
    # DigestMethod
    etree.SubElement(reference, f'{{{DSMAP["ds"]}}}DigestMethod', Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-256")
    # DigestValue
    digest_value = etree.SubElement(reference, f'{{{DSMAP["ds"]}}}DigestValue')

    # Вычисляем DigestValue от данных после преобразований
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert certs.Count != 0, "Certificates with private key not found"
    
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
    # ВАЖНО: Подписываем SignedInfo, а не данные!
    signed_info_c14n = etree.tostring(signed_info, method='c14n', exclusive=True)
    signed_info_b64 = base64.b64encode(signed_info_c14n).decode('utf-8')
    
    signed_data = pycades.SignedData()
    hashed_signed_info = pycades.HashedData()
    hashed_signed_info.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashed_signed_info.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashed_signed_info.Hash(signed_info_b64)
    # Подписываем SignedInfo
    signature_bytes = signed_data.SignHash(hashed_signed_info, signer, pycades.CADESCOM_CADES_BES, True)
    signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
 
    signature_value = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}SignatureValue')
    signature_value.text = signature_b64
    # KeyInfo
    insert_certificate_info(signature, certs.Item(1))


def insert_certificate_info(signature_element, cert):
    key_info = etree.SubElement(signature_element, f'{{{DSMAP["ds"]}}}KeyInfo')
    x509_data = etree.SubElement(key_info, f'{{{DSMAP["ds"]}}}X509Data')
    x509_certificate = etree.SubElement(x509_data, f'{{{DSMAP["ds"]}}}X509Certificate')
    x509_certificate.text = cert.Export(pycades.CAPICOM_ENCODE_BASE64).replace('\n', '')


def insert_sign(template):
    request_data = template.find(f'.//{{{NSMAP["ns"]}}}RequestData[@id="body"]')
    
    # Сериализуем исходные данные (без преобразований)
    original_data = etree.tostring(request_data, encoding='utf-8')
    
    # Вычисляем DigestValue от исходных данных
    # Преобразования будут указаны в Transforms и применены при проверке
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert certs.Count != 0, "Certificates with private key not found"
    
    hashed_data = pycades.HashedData()
    hashed_data.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashed_data.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashed_data.Hash(base64.b64encode(original_data).decode('utf-8'))
    
    hash_bytes = bytes.fromhex(hashed_data.Value)
    hash_base64 = base64.b64encode(hash_bytes).decode('utf-8')
    
    insert_signature_block(template, hash_base64)

def insert_signature_block(template, digest_value):
    caller_signature = template.find(f'.//{{{NSMAP["ns"]}}}CallerSignature')
    signature = etree.SubElement(caller_signature, f'{{{DSMAP["ds"]}}}Signature', nsmap=DSMAP)

    signed_info = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}SignedInfo')

    # CanonicalizationMethod
    etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}CanonicalizationMethod', 
                    Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    
    # SignatureMethod
    etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}SignatureMethod', 
                    Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34102012-gostr34112012-256")
    
    # Reference
    reference = etree.SubElement(signed_info, f'{{{DSMAP["ds"]}}}Reference', URI="#body")
    transforms = etree.SubElement(reference, f'{{{DSMAP["ds"]}}}Transforms')
    
    # Указываем преобразования в правильном порядке
    etree.SubElement(transforms, f'{{{DSMAP["ds"]}}}Transform', 
                    Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")
    etree.SubElement(transforms, f'{{{DSMAP["ds"]}}}Transform', 
                    Algorithm="urn://smev-gov-ru/xmldsig/transform")
    
    # DigestMethod
    etree.SubElement(reference, f'{{{DSMAP["ds"]}}}DigestMethod', 
                    Algorithm="urn:ietf:params:xml:ns:cpxmlsec:algorithms:gostr34112012-256")
    
    # DigestValue (от исходных данных)
    digest_element = etree.SubElement(reference, f'{{{DSMAP["ds"]}}}DigestValue')
    digest_element.text = digest_value

    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert certs.Count != 0, "Certificates with private key not found"

    # Подписываем SignedInfo
    signer = pycades.Signer()
    signer.Certificate = certs.Item(1)
    signer.CheckCertificate = True

    signed_info_c14n = etree.tostring(signed_info, method='c14n', exclusive=True)
    signed_info_b64 = base64.b64encode(signed_info_c14n).decode('utf-8')
    
    signed_data = pycades.SignedData()
    hashed_signed_info = pycades.HashedData()
    hashed_signed_info.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashed_signed_info.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashed_signed_info.Hash(signed_info_b64)
    
    signature_bytes = signed_data.SignHash(hashed_signed_info, signer, pycades.CADESCOM_CADES_BES, True)
    signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')

    signature_value = etree.SubElement(signature, f'{{{DSMAP["ds"]}}}SignatureValue')
    signature_value.text = signature_b64

    insert_certificate_info(signature, certs.Item(1))


def check_embedded_license():
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    
    certs = store.Certificates
    if certs.Count == 0:
        print("Сертификаты не найдены")
        return
    
    cert = certs.Item(1)
    print(f"Сертификат: {cert.SubjectName}")
    print(f"Серийный номер: {cert.SerialNumber}")
    
    # Проверяем расширения
    oid = "1.2.643.2.2.49.2"  # Example OID for an embedded license
    if cert.HasExtension(oid):
        extension_value = cert.GetExtensionValue(oid)
        print(extension_value)
    # extensions = cert.Extensions
    # for j in range(extensions.Count):
    #     ext = extensions.Item(j)
    #     if "1.2.643.2.2.49.2" in ext.OID or "встроенная лицензия" in ext.Name.lower():
    #         print("✅ Найдена встроенная лицензия!")
    #         print(f"Расширение: {ext.Name}")
    #         print(f"OID: {ext.OID}")
    #         print(f"Данные: {ext.Value}")
    #         return
    
    print("❌ Встроенная лицензия не найдена в этом сертификате\n")

