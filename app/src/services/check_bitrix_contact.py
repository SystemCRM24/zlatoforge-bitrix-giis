
from lxml import etree  # type:ignore

from src.bitrix import BitrixRepository
from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces
from src.schemas.bitrix import BitrixContact
from src.utils import logger

from .notificator import Notificator
from .service_validator import ServiceException, ServiceValidator


async def check_bitrix_contact(contact_id: str, user_id: str | None) -> bool | None:
    """Проверяет контакт в битрикс24 и отправляет уведомление пользователю."""
    try:
        contact = await BitrixRepository.get_bitrix_contact(contact_id)
        client = f"{contact.last_name} {contact.name}"
        Notificator.send_check_rfm(user_id, client)
        ServiceValidator.check_birthdate(contact)
        ServiceValidator.check_passport_data(contact)
        soap_message = get_send_get_personal_verify_rfm_message(contact)
        handler = DMDKHandler(soap_message)
        await handler.process()
        check_handler = handler.create_check_request()
        await check_handler.process(True)
        result_node = check_handler.response.find(f".//{{{namespaces.NS}}}result")
        status_node = result_node.find(f".//{{{namespaces.NS}}}status")
        status = status_node.text
        msg = f"Клиент {contact.last_name} {contact.name} проверен.\nСтатус: {status}"
        Notificator.send_message(user_id, msg)
        return status != "IS_NOT_TERRORIST"
    except ServiceException as e:
        Notificator.send_message(user_id, str(e))
    except Exception as e:
        Notificator.send_message(user_id, f"Внутренняя ошибка сервиса: {e}")
        logger.exception(str(e))


def get_send_get_personal_verify_rfm_message(contact: BitrixContact) -> SignedXMLMessage:
    """Собираем сообщение для отправки в DMDK."""
    ns = namespaces.NS
    ns1 = namespaces.CONTRACTOR
    ns2 = namespaces.DOCUMENT
    message = SignedXMLMessage("SendGetPersonalVerifyRFM", ns, ns1, ns2)
    preson_node = etree.SubElement(message.request_data, f"{{{ns}}}person")
    family_name_node = etree.SubElement(preson_node, f"{{{ns1}}}familyName")
    family_name_node.text = contact.last_name
    first_name_node = etree.SubElement(preson_node, f"{{{ns1}}}firstName")
    first_name_node.text = contact.name
    birth_day_node = etree.SubElement(preson_node, f"{{{ns1}}}birthDay")
    birth_day_node.text = contact.birth_date.date().isoformat()  # type:ignore
    identity_document_node = etree.SubElement(preson_node, f"{{{ns1}}}identityDocument")
    doc_type_node = etree.SubElement(identity_document_node, f"{{{ns2}}}docType")
    doc_type_node.text = "PASSPORT"
    serial_node = etree.SubElement(identity_document_node, f"{{{ns2}}}serial")
    serial_node.text = contact.passport_serial
    number_node = etree.SubElement(identity_document_node, f"{{{ns2}}}number")
    number_node.text = contact.passport_number
    issue_date_node = etree.SubElement(identity_document_node, f"{{{ns2}}}issueDate")
    issue_date_node.text = contact.passport_issue_date.date().isoformat()  # type:ignore
    issuer_node = etree.SubElement(identity_document_node, f"{{{ns2}}}issuer")
    issuer_node.text = contact.passport_issuer
    return message
