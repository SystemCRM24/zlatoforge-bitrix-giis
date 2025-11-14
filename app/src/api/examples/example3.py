"""Тут тестируем создание квитанции с паспортными данными."""

from datetime import date

from fastapi import APIRouter
from lxml import etree  # type:ignore

from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces


router = APIRouter(prefix="")


def get_send_buyingup_message() -> SignedXMLMessage:
    """Собираем сообщение вместе с паспортным данными."""
    ns = namespaces.NS
    ns1 = namespaces.CONTRACTOR
    ns2 = namespaces.BYINGUP
    ns3 = namespaces.DOCUMENT
    message = SignedXMLMessage("SendBuyingup", ns, ns1, ns2, ns3)
    receipt_node = etree.SubElement(message.request_data, f"{{{ns}}}receipt")
    type_node = etree.SubElement(receipt_node, f"{{{ns2}}}type")
    type_node.text = "DT_RECEIPT_FOR_REPAIR"
    state_node = etree.SubElement(receipt_node, f"{{{ns2}}}state")
    state_node.text = "DS_DRAFT"
    accept_date_node = etree.SubElement(receipt_node, f"{{{ns2}}}acceptDate")
    accept_date_node.text = date.today().isoformat()
    client_node = etree.SubElement(receipt_node, f"{{{ns2}}}client")
    family_name_node = etree.SubElement(client_node, f"{{{ns1}}}familyName")
    family_name_node.text = "Мельников"
    first_name_node = etree.SubElement(client_node, f"{{{ns1}}}firstName")
    first_name_node.text = "Максим"
    birth_day_node = etree.SubElement(client_node, f"{{{ns1}}}birthDay")
    birth_day_node.text = date(1979, 3, 2).isoformat()
    nationality_node = etree.SubElement(client_node, f"{{{ns1}}}nationality")
    nationality_node.text = "643"
    identity_document_node = etree.SubElement(client_node, f"{{{ns1}}}identityDocument")
    doc_type_node = etree.SubElement(identity_document_node, f"{{{ns3}}}docType")
    doc_type_node.text = "PASSPORT"

    message.sign()

    with open("/app/logs/send-request.xml", mode="wb") as file:
        file.write(message.to_bytes(pretty_print=True))
    return message


@router.get("/send_buyingup_wpassword")
async def send_buyingup_wpassword() -> list[str]:
    """Тут тестируем создание квитанции с паспортными данными."""
    message = get_send_buyingup_message()
    handler = DMDKHandler(message)
    response = await handler.process()
    with open("/app/logs/send-response.xml", mode="wb") as file:
        file.write(etree.tostring(response, pretty_print=True, encoding="utf-8"))
    check_handler = handler.create_check_request()
    if check_handler:
        with open("/app/logs/check-request.xml", mode="wb") as file:
            file.write(check_handler.message.to_bytes(pretty_print=True))
        response = await check_handler.process(True)
        with open("/app/logs/check-response.xml", mode="wb") as file:
            file.write(etree.tostring(response, pretty_print=True, encoding="utf-8"))
        return check_handler.response_to_list()
    return ["Hello world"]
