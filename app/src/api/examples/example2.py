"""
Здесь тестировал создание квитанции на ремонт ЮИ без введения паспортных данных.
"""

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
    type_node.text = "DT_RECEIPT_FOR_REPAIR"
    state_node = etree.SubElement(receipt_node, f"{{{ns2}}}state")
    state_node.text = "DS_DRAFT"
    accept_date_node = etree.SubElement(receipt_node, f"{{{ns2}}}acceptDate")
    accept_date_node.text = date.today().isoformat()
    client_node = etree.SubElement(receipt_node, f"{{{ns2}}}client")
    # Инфа о клиенте
    family_name_node = etree.SubElement(client_node, f"{{{ns1}}}familyName")
    family_name_node.text = "Сын маминой подруги"
    first_name_node = etree.SubElement(client_node, f"{{{ns1}}}firstName")
    first_name_node.text = "Старший"
    birth_day_node = etree.SubElement(client_node, f"{{{ns1}}}birthDay")
    birth_day_node.text = date(1984, 9, 11).isoformat()
    nationality_node = etree.SubElement(client_node, f"{{{ns1}}}nationality")
    nationality_node.text = "643"
    identity_document_node = etree.SubElement(client_node, f"{{{ns1}}}identityDocument")
    doc_type_node = etree.SubElement(identity_document_node, f"{{{ns3}}}docType")
    doc_type_node.text = "WITHOUT_DOCUMENT"
    main_address_node = etree.SubElement(client_node, f"{{{ns1}}}address")
    address_type_node = etree.SubElement(main_address_node, f"{{{ns1}}}adressType")
    address_type_node.text = "PHYS_REGISTRATION_ADDRESS"
    sub_address_node = etree.SubElement(main_address_node, f"{{{ns1}}}address")
    country_code_node = etree.SubElement(sub_address_node, f"{{{ns1}}}countryCode")
    country_code_node.text = "643"
    outer_address_node = etree.SubElement(sub_address_node, f"{{{ns1}}}outerAddress")
    outer_address_node.text = "РФ, Киров, ул Московская д1."
    description_node = etree.SubElement(receipt_node, f"{{{ns2}}}description")
    description_node.text = "Тестовая квитанция"
    message.sign()
    # Сохраним собранный xml-документ в файл.
    with open("/app/logs/send-request.xml", mode="wb") as file:
        file.write(message.to_bytes(pretty_print=True))
    return message


@router.get("/send_byingup")
async def send_byingup() -> list:
    """Тестим создание квитанции"""
    message = get_send_byingup_message()
    handler = DMDKHandler(message)
    response = await handler.process()
    with open("/app/logs/send-response.xml", mode="wb") as file:
        file.write(etree.tostring(response, pretty_print=True))
    check_handler = handler.create_check_request()
    if check_handler:
        with open("/app/logs/check-request.xml", mode="wb") as file:
            file.write(check_handler.message.to_bytes(pretty_print=True))
        response = await check_handler.process(True)
        with open("/app/logs/check-response.xml", mode="wb") as file:
            file.write(etree.tostring(response, pretty_print=True, encoding="utf-8"))
        return check_handler.response_to_list()
    return []


def get_send_batch_buyingup_out_message() -> SignedXMLMessage:
    """Собираем сообщение для на добавление готовой продукции в квитанцию"""
    endpoint = "SendBatchBuyingup"
    ns = namespaces.NS
    ns1 = namespaces.BYINGUP
    ns2 = namespaces.BATCH
    ns3 = namespaces.CONTRACTOR
    ns4 = namespaces.DOCUMENT
    ns5 = namespaces.BATCH_OPERATOR
    message = SignedXMLMessage(endpoint, ns, ns1, ns2, ns3, ns4, ns5)
    receipt_node = etree.SubElement(message.request_data, f"{{{ns}}}receipt")
    id_node = etree.SubElement(receipt_node, f"{{{ns1}}}id")
    id_node.text = "P-02-000007866-25"
    replace_node = etree.SubElement(receipt_node, f"{{{ns1}}}replace")
    replace_node.text = "false"
    batch_list_node = etree.SubElement(receipt_node, f"{{{ns1}}}batchList")
    index_node = etree.SubElement(batch_list_node, f"{{{ns2}}}index")
    index_node.text = "001"
    # Данные о продукции
    name_node = etree.SubElement(batch_list_node, f"{{{ns2}}}name")
    name_node.text = "Цепь золотая"
    type_node = etree.SubElement(batch_list_node, f"{{{ns2}}}type")
    type_node.text = "PRODUCT"
    sub_type_node = etree.SubElement(batch_list_node, f"{{{ns2}}}subType")
    sub_type_node.text = "JEWERLY"
    category_node = etree.SubElement(batch_list_node, f"{{{ns2}}}category")
    category_node.text = "JT_CHAIN"
    phase_node = etree.SubElement(batch_list_node, f"{{{ns2}}}phase")
    phase_node.text = "JEWELRY_REPAIR"
    process_node = etree.SubElement(batch_list_node, f"{{{ns2}}}process")
    process_node.text = "STORED"
    okpd2_node = etree.SubElement(batch_list_node, f"{{{ns2}}}OKPD2")
    okpd2_node.text = "32.12.13.110"
    producer_node = etree.SubElement(batch_list_node, f"{{{ns2}}}producer")
    legal_node = etree.SubElement(producer_node, f"{{{ns3}}}legal")
    ogrn_node = etree.SubElement(legal_node, f"{{{ns3}}}OGRN")
    ogrn_node.text = "0000000000000"
    kpp_node = etree.SubElement(legal_node, f"{{{ns3}}}KPP")
    kpp_node.text = "000000000"
    owner_node = etree.SubElement(batch_list_node, f"{{{ns2}}}owner")
    legal_node = etree.SubElement(owner_node, f"{{{ns3}}}legal")
    ogrn_node = etree.SubElement(legal_node, f"{{{ns3}}}OGRN")
    ogrn_node.text = "0000000000000"
    kpp_node = etree.SubElement(legal_node, f"{{{ns3}}}KPP")
    kpp_node.text = "000000000"
    quantity_node = etree.SubElement(batch_list_node, f"{{{ns2}}}quantity")
    quantity_node.text = "1"
    weight_node = etree.SubElement(batch_list_node, f"{{{ns2}}}weight")
    weight_node.text = "137000"
    uom_node = etree.SubElement(batch_list_node, f"{{{ns2}}}uom")
    uom_node.text = "GRM"
    batch_product_node = etree.SubElement(batch_list_node, f"{{{ns2}}}batchProduct")
    metal_node = etree.SubElement(batch_product_node, f"{{{ns2}}}metal")
    metal_node.text = "DM_GOLD"
    hallmark_node = etree.SubElement(batch_product_node, f"{{{ns2}}}hallmark")
    hallmark_node.text = "585"
    metal_list_node = etree.SubElement(batch_product_node, f"{{{ns2}}}metalList")
    metal_node = etree.SubElement(metal_list_node, f"{{{ns2}}}metal")
    metal_node.text = "DM_GOLD"
    weight_node = etree.SubElement(metal_list_node, f"{{{ns2}}}weight")
    weight_node.text = "80000"
    cost_list_node = etree.SubElement(batch_list_node, f"{{{ns2}}}costList")
    type_node = etree.SubElement(cost_list_node, f"{{{ns2}}}type")
    type_node.text = "P_GRM"
    currency_node = etree.SubElement(cost_list_node, f"{{{ns2}}}currency")
    currency_node.text = "RUB"
    amount_node = etree.SubElement(cost_list_node, f"{{{ns2}}}amount")
    amount_node.text = "28000000"
    rate_VAT_node = etree.SubElement(cost_list_node, f"{{{ns2}}}rateVAT")
    rate_VAT_node.text = "NDS_0"

    with open("/app/logs/send-request.xml", mode="wb") as file:
        file.write(message.to_bytes(pretty_print=True))
    return message


@router.get("/send_batch_buyingup_out")
async def send_batch_buyingup_out():
    """Метод для добавления готовой продукции в квитанцию на ремонт/изготовление ЮИ"""
    message = get_send_batch_buyingup_out_message()
    handler = DMDKHandler(message)
    response = await handler.process()
    with open("/app/logs/send-response.xml", mode="wb") as file:
        file.write(etree.tostring(response, pretty_print=True, encoding="utf-8"))
    check_handler = handler.create_check_request()
    if check_handler:
        response = await check_handler.process(True)
        with open("/app/logs/send-response.xml", mode="wb") as file:
            file.write(etree.tostring(response, pretty_print=True, encoding="utf-8"))
        return check_handler.response_to_list()
    return []
