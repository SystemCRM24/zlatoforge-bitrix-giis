import asyncio

from lxml import etree  # type:ignore

from src.bitrix import BitrixRepository
from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces
from src.schemas.bitrix import ContactSchema, DealSchema, DMDKULSchema
from src.utils import logger

from .notificator import Notificator
from .service_validator import ServiceException, ServiceValidator


async def create_production_receipt(deal_id: str, user_id: str, contour: str):
    """Создание квитанции на изготовление ювелирных изделий."""
    try:
        Notificator.send_create_production_receipt(user_id, deal_id)
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(BitrixRepository.get_deal(deal_id))
            t2 = tg.create_task(BitrixRepository.get_dmdk_lists_element_from_deal(deal_id))
        deal, dmdks = t1.result(), t2.result()
        ServiceValidator.check_dmdkul_element(dmdks)
        contact = await BitrixRepository.get_bitrix_contact(deal.CONTACT_ID)
        receipt_id = await create_receipt_draft(contact, deal, contour)
        Notificator.send_create_receipt_result(user_id, receipt_id)
        await add_pm_to_receipt(deal, receipt_id, dmdks, contour)
        Notificator.send_create_production_receipt_result(user_id, receipt_id)
        return True
    except ServiceException as e:
        Notificator.send_message(user_id, str(e))
    except Exception as e:
        Notificator.send_message(user_id, f"Внутренняя ошибка сервиса: {e}")
        logger.exception(str(e))


async def create_receipt_draft(contact, deal, contour) -> str:
    """Создаем черновик квитанции на изготовление ювелирных изделий."""
    ServiceValidator.check_contact_address(contact)
    # ServiceValidator.check_birthdate(contact)
    soap_message = get_send_byingup_message(contact, deal)
    handler = DMDKHandler(soap_message, contour)
    await handler.process()
    check_handler = handler.create_check_request()
    await check_handler.process(True)
    result_node = check_handler.response.find(f".//{{{namespaces.NS}}}result")
    id_node = result_node.find(f".//{{{namespaces.NS}}}id")
    if id_node.text is None:
        client = f"{contact.LAST_NAME} {contact.NAME}"
        raise ServiceException(f"Не удалось создать черновик квитанции для клиента {client}")
    return id_node.text


def get_send_byingup_message(contact: ContactSchema, deal: DealSchema) -> SignedXMLMessage:
    """Собираем сообщение для отправки в DMDK."""
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
    accept_date_node.text = deal.DATE_CREATE.date().isoformat()
    # Информация о клиенте
    client_node = etree.SubElement(receipt_node, f"{{{ns2}}}client")
    family_name_node = etree.SubElement(client_node, f"{{{ns1}}}familyName")
    family_name_node.text = contact.LAST_NAME
    first_name_node = etree.SubElement(client_node, f"{{{ns1}}}firstName")
    first_name_node.text = contact.NAME
    if contact.SECOND_NAME:
        second_name_node = etree.SubElement(client_node, f"{{{ns1}}}secondName")
        second_name_node.text = contact.SECOND_NAME
    # birth_day_node = etree.SubElement(client_node, f"{{{ns1}}}birthDay")
    # birth_day_node.text = contact.BIRTHDATE.isoformat()  # type: ignore
    nationality_node = etree.SubElement(client_node, f"{{{ns1}}}nationality")
    nationality_node.text = "643"
    identity_document_node = etree.SubElement(client_node, f"{{{ns1}}}identityDocument")
    doc_type_node = etree.SubElement(identity_document_node, f"{{{ns3}}}docType")
    doc_type_node.text = "WITHOUT_DOCUMENT"
    address_node = etree.SubElement(client_node, f"{{{ns1}}}address")
    address_type_node = etree.SubElement(address_node, f"{{{ns1}}}adressType")
    address_type_node.text = "PHYS_REGISTRATION_ADDRESS"
    address_node = etree.SubElement(address_node, f"{{{ns1}}}address")
    country_code_node = etree.SubElement(address_node, f"{{{ns1}}}countryCode")
    country_code_node.text = "643"
    outerAddress_node = etree.SubElement(address_node, f"{{{ns1}}}outerAddress")
    outerAddress_node.text = contact.ADDRESS
    address_fact_node = etree.SubElement(client_node, f"{{{ns1}}}addressFact")
    address_fact_node.text = contact.ADDRESS
    # Дополнительные данные для квитанции
    doc_number_node = etree.SubElement(receipt_node, f"{{{ns2}}}docNumber")
    doc_number_node.text = str(deal.ID)
    doc_date_node = etree.SubElement(receipt_node, f"{{{ns2}}}docDate")
    doc_date_node.text = deal.DATE_CREATE.date().isoformat()
    description_node = etree.SubElement(receipt_node, f"{{{ns2}}}description")
    description_node.text = f"#{deal.ID} сделка в Битриксе."
    return message


async def add_pm_to_receipt(
    deal: DealSchema, receipt_id: str, dmdks: list[DMDKULSchema], contour: str
):
    """Добавляем драгоценные металлы в квитанцию."""
    soap_message = get_send_batch_buyingup_message(deal, receipt_id, dmdks)
    handler = DMDKHandler(soap_message, contour)
    await handler.process()
    check_handler = handler.create_check_request()
    await check_handler.process(True)


def get_send_batch_buyingup_message(
    deal: DealSchema, receipt_id: str, dmdks: list[DMDKULSchema]
) -> SignedXMLMessage:
    """Собираем сообщение для дмдк с компонентами"""
    if not dmdks:
        raise ServiceException("Нет списочных элементов для добавления в квитанцию.")
    ns = namespaces.NS
    ns1 = namespaces.BYINGUP
    ns2 = namespaces.BATCH
    ns3 = namespaces.CONTRACTOR
    ns4 = namespaces.DOCUMENT
    ns5 = namespaces.BATCH_OPERATOR
    message = SignedXMLMessage("SendBatchBuyingup", ns, ns1, ns2, ns3, ns4, ns5)
    # тело сообщения
    receipt_node = etree.SubElement(message.request_data, f"{{{ns}}}receipt")
    id_node = etree.SubElement(receipt_node, f"{{{ns1}}}id")
    id_node.text = receipt_id
    replace_node = etree.SubElement(receipt_node, f"{{{ns1}}}replace")
    replace_node.text = "false"
    for index, scrap in enumerate(dmdks, start=1):
        batch_list_node = etree.SubElement(receipt_node, f"{{{ns1}}}batchList")
        # Данные по лому
        index_node = etree.SubElement(batch_list_node, f"{{{ns2}}}index")
        index_node.text = str(index).zfill(3)
        name_node = etree.SubElement(batch_list_node, f"{{{ns2}}}name")
        name_node.text = f"#{deal.ID} лом {scrap.METAL_HALLMARK}"
        description_node = etree.SubElement(batch_list_node, f"{{{ns2}}}description")
        description_node.text = scrap.NAME
        type_node = etree.SubElement(batch_list_node, f"{{{ns2}}}type")
        type_node.text = "METAL"
        sub_type_node = etree.SubElement(batch_list_node, f"{{{ns2}}}subType")
        sub_type_node.text = "SCRAP_METAL"
        phase_node = etree.SubElement(batch_list_node, f"{{{ns2}}}phase")
        phase_node.text = "BUYING_UP"
        process_node = etree.SubElement(batch_list_node, f"{{{ns2}}}process")
        process_node.text = "ACCEPTED_KEEPERED"
        OKPD2_node = etree.SubElement(batch_list_node, f"{{{ns2}}}OKPD2")
        OKPD2_node.text = scrap.OKPD_CODE
        # Данные о производителе
        producer_node = etree.SubElement(batch_list_node, f"{{{ns2}}}producer")
        legal_node = etree.SubElement(producer_node, f"{{{ns3}}}legal")
        ogrn_node = etree.SubElement(legal_node, f"{{{ns3}}}OGRN")
        ogrn_node.text = "0000000000000"  # Если производитель неизвестен
        kpp_node = etree.SubElement(legal_node, f"{{{ns3}}}KPP")
        kpp_node.text = "000000000"
        # Общие данные о партии
        quantity_node = etree.SubElement(batch_list_node, f"{{{ns2}}}quantity")
        quantity_node.text = scrap.QUANTITY
        weight_node = etree.SubElement(batch_list_node, f"{{{ns2}}}weight")
        weight_node.text = scrap.METAL_WEIGHT_EXP
        uom_node = etree.SubElement(batch_list_node, f"{{{ns2}}}uom")
        uom_node.text = "GRM"
        # Частные данные по металлу
        batch_metal_node = etree.SubElement(batch_list_node, f"{{{ns2}}}batchMetal")
        metal_node = etree.SubElement(batch_metal_node, f"{{{ns2}}}metal")
        metal_node.text = scrap.DMDK_METAL_TYPE
        metal_list_node = etree.SubElement(batch_metal_node, f"{{{ns2}}}metalList")
        hallmark_node = etree.SubElement(metal_list_node, f"{{{ns2}}}hallmark")
        hallmark_node.text = scrap.HALLMARK_EXP
        metal_node = etree.SubElement(metal_list_node, f"{{{ns2}}}metal")
        metal_node.text = scrap.DMDK_METAL_TYPE
        weight_node = etree.SubElement(metal_list_node, f"{{{ns2}}}weight")
        weight_node.text = scrap.HCM_EXP
        # Сведения о стоимости
        # Закомментировано специально, по просьбе клиента)
        # cost_list_node = etree.SubElement(batch_list_node, f"{{{ns2}}}costList")
        # type_node = etree.SubElement(cost_list_node, f"{{{ns2}}}type")
        # type_node.text = "P_PRICELIST" # Прейскурантная
        # currency_node = etree.SubElement(cost_list_node, f"{{{ns2}}}currency")
        # currency_node.text = 'RUB'
        # amount_node = etree.SubElement(cost_list_node, f"{{{ns2}}}amount")
        # amount_node.text = scrap.AMOUNT_EXP
        # rateVAT_node = etree.SubElement(cost_list_node, f"{{{ns2}}}rateVAT")
        # rateVAT_node.text = "NDS_NULL"
    return message
