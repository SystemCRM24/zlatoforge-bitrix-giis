from lxml import etree
import base64
import pycades
# from gost_xml_transform import GOSTXMLTransfosrcrm
from src.xml_schemas.gost_xml_transform.gost_xml_transform import GOSTXMLTransform



def example(xml_file: str):
    # --- Load XML ---
    tree = etree.parse(xml_file)
    root = tree.getroot()

    ns = {
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
        "wsse": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
        "wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd",
    }

    uri = "#body"
    ref_id = uri.lstrip("#")
    ref_element = root.xpath(f"//*[@id='{ref_id}']", namespaces=ns)
    if not ref_element:
        raise ValueError(f"Element with id='{ref_id}' not found")
    ref_element = ref_element[0]

    store = pycades.Store()
    store.Open(pycades.CADESCOM_CONTAINER_STORE, pycades.CAPICOM_MY_STORE, pycades.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED)
    certs = store.Certificates

    cert = certs.Item(1)

    signer = pycades.Signer()
    signer.Certificate = cert
    signer.CheckCertificate = False


    sig_node = root.find(".//ds:SignatureValue", namespaces=ns)
    if sig_node is None:
        raise ValueError("sig_node element not found")

    sig_node.text = ""

    cert_node = root.find(".//ds:X509Certificate", namespaces=ns)
    if cert_node is None:
        raise ValueError("cert_node element not found")

    b64cert = cert.Export(pycades.CADESCOM_ENCODE_BASE64)
    cert_node.text = b64cert

    c14n_bytes = etree.tostring(
        ref_element,
        method="c14n",
        exclusive=True,
        with_comments=False,
        inclusive_ns_prefixes=None,
    )

    transformer = GOSTXMLTransform.from_bytes(c14n_bytes)
    transformed_bytes = transformer.to_bytes()

    hashedData = pycades.HashedData()
    hashedData.Algorithm = pycades.CADESCOM_HASH_ALGORITHM_CP_GOST_3411_2012_256
    hashedData.DataEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    hashedData.Hash(base64.b64encode(transformed_bytes).decode())

    digestValue = base64.b64encode(bytearray.fromhex(hashedData.Value)).decode()

    reference_node = root.find(".//ds:Reference", namespaces=ns)
    if reference_node is None:
        raise ValueError("Reference element not found")

    digest_node = reference_node.find(".//ds:DigestValue", namespaces=ns)
    if digest_node is None:
        digest_node = etree.SubElement(reference_node, "{http://www.w3.org/2000/09/xmldsig#}DigestValue")

    digest_node.text = digestValue


    signed_info_node = root.find(".//ds:SignedInfo", namespaces=ns)
    if signed_info_node is None:
        raise ValueError("SignedInfo element not found")

    c14n_signed_info = etree.tostring(
        signed_info_node,
        method="c14n",
        exclusive=True,
        with_comments=False
    )


    signedData = pycades.SignedData()
    signedData.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY
    signedData.Content = base64.b64encode(c14n_signed_info).decode()
    signature = signedData.SignCades(signer, pycades.CADESCOM_CADES_BES, True)

    signatureValue =  base64.b64encode(base64.b64decode(signature)).decode()

    signature_value_node = root.find(".//ds:SignatureValue", namespaces=ns)
    if signature_value_node is None:
        signature_value_node = etree.SubElement(
            root.find(".//ds:Signature", namespaces=ns),
            "{http://www.w3.org/2000/09/xmldsig#}SignatureValue"
        )

    signature_value_node.text = signatureValue

    tree.write(xml_file, encoding="utf-8", xml_declaration=True)

    # with open("signed.xml", "r") as f:
    #     final_xml = f.read()

    # signedXML = pycades.SignedXML()
    # signedXML.Verify(final_xml)
