from lxml import etree  # type:ignore

from src.bitrix import BitrixRepository
from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces
from src.schemas.bitrix import ContactSchema
from src.utils import logger

from .notificator import Notificator
from .service_validator import ServiceException, ServiceValidator


async def check_bitrix_contact(contact_id: str, user_id: str) -> bool | None:
    """Проверяет контакт в битрикс24 и отправляет уведомление пользователю."""
    try:
        contact = await BitrixRepository.get_bitrix_contact(contact_id)
        client = f"{contact.LAST_NAME} {contact.NAME}"
        Notificator.send_check_rfm(user_id, client)
        ServiceValidator.check_birthdate(contact)
        ServiceValidator.check_passport_data(contact, "check")
        soap_message = get_send_get_personal_verify_rfm_message(contact)
        handler = DMDKHandler(soap_message, contour="work")
        await handler.process()
        check_handler = handler.create_check_request()
        await check_handler.process(True)
        result_node = check_handler.response.find(f".//{{{namespaces.NS}}}result")
        status_node = result_node.find(f".//{{{namespaces.NS}}}status")
        status = status_node.text
        Notificator.send_check_rfm_result(user_id, client, status)
        return status != "IS_NOT_TERRORIST"
    except ServiceException as e:
        Notificator.send_message(user_id, str(e))
    except Exception as e:
        Notificator.send_message(user_id, f"Внутренняя ошибка сервиса: {e}")
        logger.exception(str(e))


def get_send_get_personal_verify_rfm_message(contact: ContactSchema) -> SignedXMLMessage:
    """Собираем сообщение для отправки в DMDK."""
    ns = namespaces.NS
    ns1 = namespaces.CONTRACTOR
    ns2 = namespaces.DOCUMENT
    message = SignedXMLMessage("SendGetPersonalVerifyRFM", ns, ns1, ns2)
    preson_node = etree.SubElement(message.request_data, f"{{{ns}}}person")
    family_name_node = etree.SubElement(preson_node, f"{{{ns1}}}familyName")
    family_name_node.text = contact.LAST_NAME
    first_name_node = etree.SubElement(preson_node, f"{{{ns1}}}firstName")
    first_name_node.text = contact.NAME
    birth_day_node = etree.SubElement(preson_node, f"{{{ns1}}}birthDay")
    birth_day_node.text = contact.BIRTHDATE.isoformat()  # type:ignore
    identity_document_node = etree.SubElement(preson_node, f"{{{ns1}}}identityDocument")
    doc_type_node = etree.SubElement(identity_document_node, f"{{{ns2}}}docType")
    doc_type_node.text = "PASSPORT"
    serial_node = etree.SubElement(identity_document_node, f"{{{ns2}}}serial")
    serial_node.text = contact.PASSPORT_SERIAL
    number_node = etree.SubElement(identity_document_node, f"{{{ns2}}}number")
    number_node.text = contact.PASSPORT_NUMBER
    issue_date_node = etree.SubElement(identity_document_node, f"{{{ns2}}}issueDate")
    issue_date_node.text = contact.PASSPORT_ISSUE_DATE.isoformat()  # type:ignore
    issuer_node = etree.SubElement(identity_document_node, f"{{{ns2}}}issuer")
    issuer_node.text = contact.PASSPORT_ISSUER
    return message
