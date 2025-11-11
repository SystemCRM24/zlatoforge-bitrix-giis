from datetime import date

from fastapi import APIRouter
from lxml import etree  # type:ignore

from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces


router = APIRouter(prefix="")


def get_send_byingup_message() -> SignedXMLMessage:
    """Собираем сообщение"""
    ns = namespaces.NS
    ns1 = namespaces.CONTRACTOR
    ns2 = namespaces.BYINGUP
    ns3 = namespaces.DOCUMENT
    message = SignedXMLMessage("SendBuyingup", ns, ns1, ns2, ns3)
    receipt_node = etree.SubElement(message.request_data, f"{{{ns}}}receipt")
    type_node = etree.SubElement(receipt_node, f"{{{ns2}}}type")
    type_node.text = "DT_RECEIPT_FOR_MANUFACTURING"
    state_node = etree.SubElement(receipt_node, f"{{{ns2}}}state")
    state_node.text = "DS_DRAFT"
    accept_date_node = etree.SubElement(receipt_node, f"{{{ns2}}}acceptDate")
    accept_date_node.text = date.today().isoformat()
    client_node = etree.SubElement(receipt_node, f"{{{ns2}}}client")
    amount_node = etree.SubElement(receipt_node, f"{{{ns2}}}amount")
    amount_node.text = "100"
    currency_node = etree.SubElement(receipt_node, f"{{{ns2}}}currency")
    currency_node.text = "RUB"
    # Инфа о клиенте
    family_name_node = etree.SubElement(client_node, f"{{{ns1}}}familyName")
    family_name_node.text = "Старший"
    first_name_node = etree.SubElement(client_node, f"{{{ns1}}}firstName")
    first_name_node.text = "Сын маминой Подруги"
    birth_day_node = etree.SubElement(client_node, f"{{{ns1}}}birthDay")
    birth_day_node.text = date(1984, 9, 11).isoformat()
    identity_document_node = etree.SubElement(client_node, f"{{{ns1}}}identityDocument")
    doc_type_node = etree.SubElement(identity_document_node, f"{{{ns3}}}docType")
    doc_type_node.text = "WITHOUT_DOCUMENT"
    message.sign()
    # Сохраним собранный xml-документ в файл.
    with open("/app/logs/request.xml", mode="wb") as file:
        file.write(message.to_bytes(pretty_print=True))
    return message


@router.get("/send_byingup")
async def send_byingup() -> bool:
    """Тестим создание квитанции"""
    message = get_send_byingup_message()
    handler = DMDKHandler(message)
    response = await handler.process()
    with open("/app/logs/response.xml", mode="wb") as file:
        file.write(etree.tostring(response, pretty_print=True))
    return True
