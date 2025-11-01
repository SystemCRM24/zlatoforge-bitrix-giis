import pycades
import base64
import hashlib
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def create_xmldsig_with_digest(data_to_sign, cert_thumbprint):
    """
    Создание полного XMLDSig документа с DigestValue
    """
    try:
        # 1. Вычисляем DigestValue
        digest_value = calculate_digest_value(data_to_sign)
        
        # # 2. Создаем подпись через pycades
        signature_value = create_signature_value(data_to_sign, cert_thumbprint)
        
        # 3. Получаем информацию о сертификате
        cert_info = get_certificate_info(cert_thumbprint)
        
        # 4. Формируем XML документ
        xmldsig = build_xmldsig_document(
            data_to_sign, 
            digest_value, 
            signature_value, 
            cert_info
        )
        
        return xmldsig
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def calculate_digest_value(data):
    """
    Вычисление DigestValue по алгоритму SHA-256
    """
    # Вычисляем хеш
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    digest = hashlib.sha256(data).digest()
    digest_b64 = base64.b64encode(digest).decode('utf-8')
    
    return digest_b64

def create_signature_value(data, cert_thumbprint):
    """
    Создание значения подписи через pycades
    """
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates
    assert(certs.Count != 0), "Certificates with private key not found"
    signer = pycades.Signer()
    signer.Certificate = certs.Item(1)
    signer.CheckCertificate = True
    signed_data = pycades.SignedData()
    signed_data.Content = data
    signed_data.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    signature = signed_data.SignCades(signer, pycades.CADESCOM_CADES_BES)
    return signature

def get_certificate_info(cert_thumbprint):
    """
    Получение информации о сертификате
    """
    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, 
              pycades.CAPICOM_MY_STORE, 
              pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    
    certificates = store.Certificates
        
    cert = certificates.Item(1)
    
    return {
        'serial_number': cert.SerialNumber,
        'issuer_name': cert.IssuerName,
        'subject_name': cert.SubjectName,
        'cert_data': cert.Export(pycades.CAPICOM_ENCODE_BASE64)
    }

def build_xmldsig_document(data, digest_value, signature_value, cert_info):
    """
    Построение полного XMLDSig документа
    """
    # Создаем корневой элемент Signature
    signature = Element('Signature', xmlns='http://www.w3.org/2000/09/xmldsig#')
    
    # SignedInfo section
    signed_info = SubElement(signature, 'SignedInfo')
    SubElement(signed_info, 'CanonicalizationMethod', Algorithm='http://www.w3.org/2001/10/xml-exc-c14n#')
    SubElement(signed_info, 'SignatureMethod', Algorithm='http://www.w3.org/2001/04/xmldsig-more#gostr34102001-gostr3411')
    
    # Reference section with DigestValue
    reference = SubElement(signed_info, 'Reference', URI='')
    transforms = SubElement(reference, 'Transforms')
    SubElement(transforms, 'Transform', Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature')
    
    digest_method = SubElement(reference, 'DigestMethod', Algorithm='http://www.w3.org/2001/04/xmlenc#sha256')
    digest_value_elem = SubElement(reference, 'DigestValue')
    digest_value_elem.text = digest_value  # Вот наш DigestValue!
    
    # SignatureValue
    signature_value_elem = SubElement(signature, 'SignatureValue')
    signature_value_elem.text = signature_value
    
    # KeyInfo
    key_info = SubElement(signature, 'KeyInfo')
    x509_data = SubElement(key_info, 'X509Data')
    x509_certificate = SubElement(x509_data, 'X509Certificate')
    x509_certificate.text = cert_info['cert_data']
    
    # Форматируем XML для красивого вывода
    rough_string = tostring(signature, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    
    return reparsed.toprettyxml(indent="  ")

# Альтернативный вариант - получение DigestValue из подписанных данных
def get_digest_from_signed_data(data_to_sign):
    """
    Альтернативный способ получения DigestValue через pycades
    """
    try:
        signed_data = pycades.SignedData()
        signed_data.Content = base64.b64encode(data_to_sign.encode('utf-8')).decode('utf-8')
        signed_data.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
        
        # В некоторых реалиях можно получить хеш через SignedData
        # Но обычно проще вычислить самостоятельно
        
        return calculate_digest_value(data_to_sign)
        
    except Exception as e:
        print(f"Ошибка получения DigestValue: {e}")
        return None

# Пример использования
if __name__ == "__main__":
    data = "Важные данные для подписи"
    thumbprint = "A1B2C3D4E5F6..."  # Ваш отпечаток
    
    # Создаем полный XMLDSig документ
    xmldsig_doc = create_xmldsig_with_digest(data, thumbprint)
    
    if xmldsig_doc:
        print("XMLDSig документ создан:")
        print(xmldsig_doc)
        
        # Сохраняем в файл
        with open('signature.xml', 'w', encoding='utf-8') as f:
            f.write(xmldsig_doc)