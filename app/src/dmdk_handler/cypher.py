import base64

import pycades  # type:ignore


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


def dmdk_hash(string: bytes) -> str:
    """Высчитывает хеш от строки по стандарту XMLSign, который используется дмдк."""
    b64_string = base64.b64encode(string).decode()
    hashedData = pycades.HashedData()
    hashedData.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashedData.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashedData.Hash(b64_string)
    # Вычесленный хеш нужно вернуть как base64 строку
    return base64.b64encode(bytearray.fromhex(hashedData.Value)).decode()


def dmdk_signature(string: bytes) -> str:
    """Высчитывает подпись от строки по стандарту XMLSign, который используется дмдк."""
    # Тут вообще жесть. Сначало считаем хеш от SignedINfo, а потом от него подпись.
    b64_string = base64.b64encode(string).decode()
    hashedData = pycades.HashedData()
    hashedData.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashedData.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashedData.Hash(b64_string)
    # Подпись
    signed_data = pycades.RawSignature()
    signature_hex: str = signed_data.SignHash(hashedData, CLIENT_CERT)
    # Переворачиваем значение, так как нужно получить число в формате BigEndian
    inverted_signature_bytes = bytearray(reversed(bytearray.fromhex(signature_hex)))
    return base64.b64encode(inverted_signature_bytes).decode("utf-8")


def get_certificate() -> str:
    """Возвращает данные сертификата как base64 строку"""
    return CLIENT_CERT.Export(pycades.CADESCOM_ENCODE_BASE64)
