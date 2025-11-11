from lxml import etree # type:ignore 
from fastapi import APIRouter

from src.dmdk_handler import DMDKHandler, SignedXMLMessage, namespaces


router = APIRouter(prefix="/examples", tags=["examples"])


# Разберем работу с ГИИС ДМДК на примере метода для получения элементов справочника. 
# Первый шаг - нам нужно сформировать запрос. Для этого используем класс SignedXMLMessage и 
# библиотеку lxml. Сам класс SignedXMLMessage реализует удобный интерфейс, позволяя сосредоточится 
# на сборке информации для запроса. Рекомендую собирать запросы в отдельных функциях.
def get_send_glossary_message() -> SignedXMLMessage:
    """Собирает xml-сообщение для получения элементов справочника."""
    # Для xml-сообщения очень важны 2 атрибута - эндпоинт, на который будет посылаться запрос и 
    # пространство имен. С эндпоинтом все просто - копируем его с документации ГИИС.
    endpoint = 'SendGetGlossary'
    # C Пространством имен чуть сложнее. Нам нужны будут те, которые используются внутри тэга 
    # RequestData примера документации. Приведу пример как это узнать. 
    # <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="urn://xsd.dmdk.goznak.ru/exchange/3.0">
    # ...
    # <ns:RequestData id="body">
    #    <ns:type>GEMSTONE_COLOR_TYPE</ns:type>
    #    <ns:page>1</ns:page>
    #    <ns:size>25</ns:size>
    # </ns:RequestData> 
    # ... 
    # Видим, что внутри используется неймспейс с алиасом ns, а значение указано в шапке. Эти 
    # значения сохранены в подмодуле namespaces. Для наглядности, можно их сохранить в переменные 
    # под используемыми алиасами.
    ns = namespaces.NS
    # Далее, инициируем объект и передаем эндпоинт и пространства имен
    message = SignedXMLMessage(endpoint, ns)
    # У объекта будет атриут - request_data. Его используем как корневой для операций добавления 
    # внутренней структуры.
    type_node = etree.SubElement(message.request_data, f"{{{ns}}}type") # тройные скобки необходимы
    type_node.text = 'GEMSTONE_COLOR_TYPE' 
    page_node = etree.SubElement(message.request_data, f"{{{ns}}}page")
    page_node.text = '1' # Только строки можно добавлять в сообщения
    size_node = etree.SubElement(message.request_data, f"{{{ns}}}size")
    size_node.text = str(500)
    # Для проверки себя, лучше сверяйте собранный и подписанный документ. До отправки запроса, 
    # сделать это можно следующим образом. DMDKHandler вызывает этот метод самостоятельно, поэтому 
    # его можно каждый раз не вызывать.
    message.sign()
    # Сохраним собранный xml-документ в файл.
    with open("/app/logs/request.xml", mode="wb") as file:
        file.write(message.to_bytes(pretty_print=True))
    return message




@router.get("/send_get_glossary")
async def send_get_glossary() -> dict:
    """Отправляем тестовый запрос к ГИИС ДМДК"""
    # 1) Получаем собранное сообщение
    message = get_send_glossary_message()
    # 2) Инициализируем объект DMDKHandler
    handler = DMDKHandler(message)
    # 3) Вызываем метод process для выполнения запроса. Метод вернет словарь, в котором будет 
    # представлены внутренняя структура ResonseData тега.
    response = await handler.process()
    # Помимо разобранных данных, сохраняется еще и сырой ответ в виде объекта etree._Element 
    # Ее можно получить по атрибуту raw_response. Cохраним этот документ в файл.
    with open("/app/logs/response.xml", mode="wb") as file:
        file.write(etree.tostring(handler.response, pretty_print=True))
    # Нужно учитывать, что методы парные. Этот метод - начальный из пары.
    # Т.е. Сначало мы отправляем запрос на обработку данных, а вторым - запрашиваем результат.
    # При успехе - первый запрос возвращает идентификатор для второго запроса. Его и будем возращать.
    # with open("/app/logs/request.xml", mode="wb") as file:
    #     file.write(handler.message.to_bytes(pretty_print=True))
    # # Далее, вызываем метод process. Под капотом он соберет сообщение, выполнит запрос и вернет
    # # ответ в виде словаря. Получить словарь также можно так: handler.response
    # response = await handler.process()
    check_handler = handler.create_check_request()
    if check_handler:
        response = await check_handler.process(True)
        with open("/app/logs/response.xml", mode="wb") as file:
            file.write(etree.tostring(check_handler.response, pretty_print=True))
        print(response)
    return {}
