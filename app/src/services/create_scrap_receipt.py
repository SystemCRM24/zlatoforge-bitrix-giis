from datetime import date

from lxml import etree  # type:ignore

from src.bitrix import BitrixRepository
from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces
from src.schemas.bitrix import BitrixContact
from src.utils import logger

from .notificator import Notificator
from .service_validator import ServiceException, ServiceValidator


async def create_scrap_receipt(contact_id: str, user_id: str):
    """Формирование квитанции на скупку лома"""
    contact_id = "35732"
    try:
        contact = await BitrixRepository.get_bitrix_contact(contact_id)
        receipt_id = await create_receipt_draft(contact, user_id)
        logger.success(receipt_id)
    except ServiceException as e:
        Notificator.send_message(user_id, str(e))
    except Exception as e:
        Notificator.send_message(user_id, f"Внутренняя ошибка сервиса: {e}")
        logger.exception(str(e))


async def create_receipt_draft(contact: BitrixContact, user_id: str) -> str:
    """Создает черновик квитанции и возвращает ее номер."""
    client = f"{contact.last_name} {contact.name}"
    Notificator.send_create_scrap_receipt(user_id, client)
    ServiceValidator.check_birthdate(contact)
    ServiceValidator.check_passport_data(contact)
    soap_message = get_send_buyingup_message(contact)
    handler = DMDKHandler(soap_message, log=True)
    await handler.process()
    check_handler = handler.create_check_request()
    await check_handler.process(True)
    result_node = check_handler.response.find(f".//{{{namespaces.NS}}}result")
    id_node = result_node.find(f".//{{{namespaces.NS}}}id")
    if id_node.text is None:
        raise ServiceException(f"Не удалось создать черновик квитанции для клиента {client}")
    return id_node.text


def get_send_buyingup_message(contact: BitrixContact) -> SignedXMLMessage:
    """Собираем сообщение на создание бланка квитанции."""
    ns = namespaces.NS
    ns1 = namespaces.CONTRACTOR
    ns2 = namespaces.BYINGUP
    ns3 = namespaces.DOCUMENT
    message = SignedXMLMessage("SendBuyingup", ns, ns1, ns2, ns3)
    receipt_node = etree.SubElement(message.request_data, f"{{{ns}}}receipt")
    type_node = etree.SubElement(receipt_node, f"{{{ns2}}}type")
    type_node.text = "DT_RECEIPT_FOR_BUYINGUP"
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
    serial_node = etree.SubElement(identity_document_node, f"{{{ns3}}}serial")
    serial_node.text = contact.passport_serial
    number_node = etree.SubElement(identity_document_node, f"{{{ns3}}}number")
    number_node.text = contact.passport_number
    issue_date_node = etree.SubElement(identity_document_node, f"{{{ns3}}}issueDate")
    issue_date_node.text = contact.passport_issue_date.date().isoformat()  # type: ignore
    issuer_node = etree.SubElement(identity_document_node, f"{{{ns3}}}issuer")
    issuer_node.text = contact.passport_issuer
    return message
