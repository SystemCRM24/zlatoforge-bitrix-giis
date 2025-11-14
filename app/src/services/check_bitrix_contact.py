import asyncio

from lxml import etree  # type:ignore

from src.bitrix import BitrixRepository
from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces
from src.schemas.bitrix import BitrixClient


async def check_bitrix_contact(contact_id: str, user_id: str | None) -> bool | None:
    """Проверяет контакт в битрикс24 и отправляет уведомление пользователю."""
    contact = await BitrixRepository.get_bitrix_contact(contact_id)
    ntf = (
        f"Осуществляется проверка клиента {contact.last_name} {contact.name} "
        "в реестрах Росфинмониторинга."
    )
    ntf_coro = BitrixRepository.send_notification(ntf, user_id)
    asyncio.create_task(ntf_coro)
    if contact.birth_date is None:
        notification = (
            f"Необходимо указать дату рождения клиента {contact.last_name} {contact.name} "
            "для осуществления проверки."
        )
        asyncio.create_task(BitrixRepository.send_notification(notification, user_id))
        return
    if not contact.check_passport_data():
        notification = (
            f"Необходимо заполнить все паспортные данные клиента {contact.last_name} {contact.name}"
            " для осуществления проверки."
        )
        asyncio.create_task(BitrixRepository.send_notification(notification, user_id))
        return
    soap_message = get_send_get_personal_verify_rfm_message(contact)
    handler = DMDKHandler(soap_message)
    await handler.process()
    check_handler = handler.create_check_request()
    if check_handler:
        await check_handler.process(True)
        result_node = check_handler.response.find(f".//{{{namespaces.NS}}}result")
        status_node = result_node.find(f".//{{{namespaces.NS}}}status")
        status = status_node.text
        msg = f"Клиент {contact.last_name} {contact.name} проверен.\nСтатус: {status}"
        asyncio.create_task(BitrixRepository.send_notification(msg))
        return status != "IS_NOT_TERRORIST"
    asyncio.create_task(BitrixRepository.send_notification("Внутренняя ошибка ДМДК"))


def get_send_get_personal_verify_rfm_message(client: BitrixClient) -> SignedXMLMessage:
    """Собираем сообщение для отправки в DMDK."""
    ns = namespaces.NS
    ns1 = namespaces.CONTRACTOR
    ns2 = namespaces.DOCUMENT
    message = SignedXMLMessage("SendGetPersonalVerifyRFM", ns, ns1, ns2)
    preson_node = etree.SubElement(message.request_data, f"{{{ns}}}person")
    family_name_node = etree.SubElement(preson_node, f"{{{ns1}}}familyName")
    family_name_node.text = client.last_name
    first_name_node = etree.SubElement(preson_node, f"{{{ns1}}}firstName")
    first_name_node.text = client.name
    birth_day_node = etree.SubElement(preson_node, f"{{{ns1}}}birthDay")
    birth_day_node.text = client.birth_date.date().isoformat()  # type:ignore
    identity_document_node = etree.SubElement(preson_node, f"{{{ns1}}}identityDocument")
    doc_type_node = etree.SubElement(identity_document_node, f"{{{ns2}}}docType")
    doc_type_node.text = "PASSPORT"
    serial_node = etree.SubElement(identity_document_node, f"{{{ns2}}}serial")
    serial_node.text = client.passport_serial
    number_node = etree.SubElement(identity_document_node, f"{{{ns2}}}number")
    number_node.text = client.passport_number
    issue_date_node = etree.SubElement(identity_document_node, f"{{{ns2}}}issueDate")
    issue_date_node.text = client.passport_issue_date.date().isoformat()  # type:ignore
    issuer_node = etree.SubElement(identity_document_node, f"{{{ns2}}}issuer")
    issuer_node.text = client.passport_issuer
    return message
