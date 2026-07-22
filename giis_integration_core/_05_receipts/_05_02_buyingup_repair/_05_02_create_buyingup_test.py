import sys
sys.path.insert(0, '/app')

import asyncio
from datetime import date
from lxml import etree
from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces

NS = namespaces.NS
NS_BUYINGUP = namespaces.BYINGUP
NS_CONTRACTOR = namespaces.CONTRACTOR
NS_DOCUMENT = namespaces.DOCUMENT

async def main():
    print("=" * 60)
    print("🧪 ТЕСТ: Квитанция на СКУПКУ с карточкой физлица (ТЕСТОВЫЙ КОНТУР)")
    print("=" * 60)

    message = SignedXMLMessage("SendBuyingup", NS, NS_BUYINGUP, NS_CONTRACTOR, NS_DOCUMENT)
    rd = message.request_data

    ns_bu = f"{{{NS_BUYINGUP}}}"
    ns_c = f"{{{NS_CONTRACTOR}}}"
    ns_d = f"{{{NS_DOCUMENT}}}"

    receipt = etree.SubElement(rd, f"{{{NS}}}receipt")
    
    etree.SubElement(receipt, f"{ns_bu}type").text = "DT_RECEIPT_FOR_BUYINGUP"
    etree.SubElement(receipt, f"{ns_bu}state").text = "DS_DRAFT"
    etree.SubElement(receipt, f"{ns_bu}acceptDate").text = date.today().isoformat()

    client = etree.SubElement(receipt, f"{ns_bu}client")
    etree.SubElement(client, f"{ns_c}familyName").text = "Петров"
    etree.SubElement(client, f"{ns_c}firstName").text = "Петр"
    etree.SubElement(client, f"{ns_c}secondName").text = "Петрович"
    
    etree.SubElement(client, f"{ns_c}birthDay").text = "1990-01-01"
    # ДОБАВЛЕНО: Гражданство (код страны, 643 = РФ)
    etree.SubElement(client, f"{ns_c}nationality").text = "643"
    
    identity_doc = etree.SubElement(client, f"{ns_c}identityDocument")
    etree.SubElement(identity_doc, f"{ns_d}docType").text = "PASSPORT"
    etree.SubElement(identity_doc, f"{ns_d}serial").text = "4500"
    etree.SubElement(identity_doc, f"{ns_d}number").text = "123456"
    etree.SubElement(identity_doc, f"{ns_d}issueDate").text = "2020-01-01"
    etree.SubElement(identity_doc, f"{ns_d}expirDate").text = "2030-01-01"
    etree.SubElement(identity_doc, f"{ns_d}issuer").text = "ОВД г. Кирова"
    
    address = etree.SubElement(client, f"{ns_c}address")
    etree.SubElement(address, f"{ns_c}adressType").text = "PHYS_REGISTRATION_ADDRESS"
    address_inner = etree.SubElement(address, f"{ns_c}address")
    etree.SubElement(address_inner, f"{ns_c}countryCode").text = "643"
    etree.SubElement(address_inner, f"{ns_c}outerAddress").text = "г. Киров, ул. Тестовая, д. 1"

    etree.SubElement(receipt, f"{ns_bu}description").text = "Тестовая квитанция на скупку"

    print("✍️ Подписываем сообщение...")
    message.sign()
    print("✅ Подпись готова")

    print(" Отправка в тестовый контур...")
    handler = DMDKHandler(message, contour="test")
    await handler.process()

    print("🔍 Проверяем статус...")
    check_handler = handler.create_check_request()
    await check_handler.process(True)

    status = check_handler.response.findtext(f".//{{{NS}}}status")
    receipt_id = check_handler.response.findtext(f".//{{{NS}}}result/{{{NS}}}id")

    print("=" * 60)
    if receipt_id:
        print(f"🎉 КВИТАНЦИЯ НА СКУПКУ СОЗДАНА!")
        print(f"📋 Номер: {receipt_id}")
        print(f"💡 Статус: {status}")
        print(f"🔗 Проверьте в ЛК: https://testlk.dmdk.ru")
    else:
        print(f"⚠️ Статус: {status}")
        print("📄 Полный ответ:")
        print(etree.tostring(check_handler.response, pretty_print=True, encoding="unicode")[:2000])
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()