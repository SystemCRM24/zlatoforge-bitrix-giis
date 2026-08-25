import traceback
import sys
from datetime import date

sys.path.insert(0, '/app')

from lxml import etree
from giis_integration_core.webhook_handler.bitrix_client import BitrixClient
from giis_integration_core.webhook_handler.notifications import notify_success, notify_error
from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces

bitrix = BitrixClient()

async def process_buyingup(deal_id: int):
    """
    Основной обработчик для создания квитанции на скупку на основе Сделки и Контакта.
    """
    print(f"🚀 Начало обработки скупки для Сделки Битрикс24 ID: {deal_id}")
    
    try:
        # 1. Забираем данные Сделки и Контакта
        print("📥 Загрузка данных из Битрикс24...")
        deal_fields = await bitrix.get_deal(deal_id)
        contact_id = deal_fields.get('CONTACT_ID')
        
        contact_fields = {}
        if contact_id:
            print(f"📥 Загрузка данных Контакта ID: {contact_id}...")
            contact_fields = await bitrix.get_contact(contact_id)

        # 2. Извлекаем реальные данные (приоритет: Контакт -> Сделка -> заглушка)
        last_name = contact_fields.get('LAST_NAME') or deal_fields.get('UF_CRM_GIIS_CLIENT_LAST_NAME') or "Петров"
        first_name = contact_fields.get('NAME') or deal_fields.get('UF_CRM_GIIS_CLIENT_FIRST_NAME') or "Петр"
        second_name = contact_fields.get('SECOND_NAME') or deal_fields.get('UF_CRM_GIIS_CLIENT_SECOND_NAME') or "Петрович"
        
        birth_day = contact_fields.get('BIRTHDATE') or deal_fields.get('UF_CRM_GIIS_CLIENT_BIRTHDAY') or "1990-01-01"
        if 'T' in str(birth_day):
            birth_day = str(birth_day).split('T')[0]
        
        passport_serial = contact_fields.get('UF_CRM_1784654964357') or deal_fields.get('UF_CRM_GIIS_CLIENT_PASSPORT_SERIAL') or "4500"
        passport_number = contact_fields.get('UF_CRM_1648298987071') or deal_fields.get('UF_CRM_GIIS_CLIENT_PASSPORT_NUMBER') or "123456"
        
        issue_date = contact_fields.get('UF_CRM_1648299623368') or deal_fields.get('UF_CRM_GIIS_CLIENT_PASSPORT_ISSUE_DATE') or "2020-01-01"
        if 'T' in str(issue_date):
            issue_date = str(issue_date).split('T')[0]
            
        issuer = contact_fields.get('UF_CRM_1648299575558') or deal_fields.get('UF_CRM_GIIS_CLIENT_PASSPORT_ISSUER') or "ОВД г. Кирова"
        
        # Адрес (берем из правильного пользовательского поля Контакта)
        address = contact_fields.get('UF_CRM_1591111034541') or contact_fields.get('ADDRESS') or deal_fields.get('UF_CRM_GIIS_CLIENT_ADDRESS') or "г. Киров, ул. Тестовая, д. 1"
        address = address.split('|;|')[0].strip() if '|;|' in address else address

        print(f"   Клиент: {last_name} {first_name} {second_name}")
        print(f"   Паспорт: {passport_serial} {passport_number}, выдан {issue_date}")
        print(f"   Адрес: {address}")

        # 3. Формируем XML сообщение (СТРОГО в порядке XSD схемы ГИИС)
        ns = namespaces.NS
        ns_contractor = namespaces.CONTRACTOR
        ns_buyingup = namespaces.BYINGUP
        ns_document = namespaces.DOCUMENT
        
        message = SignedXMLMessage("SendBuyingup", ns, ns_contractor, ns_buyingup, ns_document)
        rd = message.request_data
        
        receipt_node = etree.SubElement(rd, f"{{{ns}}}receipt")
        etree.SubElement(receipt_node, f"{{{ns_buyingup}}}type").text = "DT_RECEIPT_FOR_BUYINGUP"
        etree.SubElement(receipt_node, f"{{{ns_buyingup}}}state").text = "DS_DRAFT"
        etree.SubElement(receipt_node, f"{{{ns_buyingup}}}acceptDate").text = date.today().isoformat()
        
        client_node = etree.SubElement(receipt_node, f"{{{ns_buyingup}}}client")
        etree.SubElement(client_node, f"{{{ns_contractor}}}familyName").text = last_name
        etree.SubElement(client_node, f"{{{ns_contractor}}}firstName").text = first_name
        if second_name:
            etree.SubElement(client_node, f"{{{ns_contractor}}}secondName").text = second_name
        etree.SubElement(client_node, f"{{{ns_contractor}}}birthDay").text = birth_day
        etree.SubElement(client_node, f"{{{ns_contractor}}}nationality").text = "643"
        
        identity_doc_node = etree.SubElement(client_node, f"{{{ns_contractor}}}identityDocument")
        etree.SubElement(identity_doc_node, f"{{{ns_document}}}docType").text = "PASSPORT"
        etree.SubElement(identity_doc_node, f"{{{ns_document}}}serial").text = str(passport_serial)
        etree.SubElement(identity_doc_node, f"{{{ns_document}}}number").text = str(passport_number)
        etree.SubElement(identity_doc_node, f"{{{ns_document}}}issueDate").text = issue_date
        etree.SubElement(identity_doc_node, f"{{{ns_document}}}issuer").text = issuer
        
        etree.SubElement(client_node, f"{{{ns_contractor}}}addressFact").text = address
        etree.SubElement(receipt_node, f"{{{ns_buyingup}}}description").text = f"Сделка #{deal_id} в Битриксе."

        # 4. Отправляем в ГИИС ДМДК
        print("✍️ Подписываем и отправляем сообщение в ГИИС ДМДК (тестовый контур)...")
        handler = DMDKHandler(message, contour="test")
        await handler.process()
        
        print("🔍 Ожидаем обработки и проверяем статус...")
        check_handler = handler.create_check_request()
        await check_handler.process(True)
        
        # 5. Извлекаем ID квитанции из ответа
        result_node = check_handler.response.find(f".//{{{ns}}}result")
        if result_node is not None:
            id_node = result_node.find(f".//{{{ns}}}id")
            if id_node is not None and id_node.text:
                receipt_id = id_node.text
                print(f"🎉 Успех! Квитанция {receipt_id} создана.")
                
                # ВАЖНО: вызываем асинхронную функцию с await
                await notify_success(deal_id, receipt_id, "Скупка")
                
                return receipt_id
        
        error_msg = "Квитанция не создана: не удалось получить ID из ответа ГИИС"
        print(f"❌ {error_msg}")
        await notify_error(deal_id, error_msg, "Скупка")
        return None

    except Exception as e:
        error_msg = str(e)
        print(f"🚨 ТИП ОШИБКИ: {type(e).__name__}\n{traceback.format_exc()}")
        print(f"❌ Критическая ошибка обработки: {error_msg}")
        await notify_error(deal_id, error_msg, "Скупка")
        return None