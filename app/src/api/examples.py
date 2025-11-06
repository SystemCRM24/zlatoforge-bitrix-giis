from fastapi import APIRouter

from src.dmdk_handler import DMDKHandler, Node
from src.dmdk_handler import namespaces as NS


router = APIRouter(prefix="/examples", tags=["examples"])


@router.get("/send_get_glossary")
async def send_get_glossary() -> dict:
    """
    Нужно учитывать, что методы парные. Этот метод - начальный из пары.
    Т.е. Сначало мы отправляем запрос на обработку данных, а вторым - запрашиваем результат.
    При успехе - первый запрос возвращает идентификатор для второго запроса. Его и будем возращать.
    Смотри комментарии к коду ниже.
    """
    # 1) Нужно сформировать внутреннюю структуру сообщения. Делаем это через класс Node.
    # Всегда начинаем с корневой структуры RequestData. В принципе, ей можно дать любое название и
    # пространство имен. Обработчик это сам исправит, так как эту ноду расположить в структуре
    # xml-документа определенным образом. Для всех остальных нод, которые будут вкладываться в
    # корневую это обязательно, поэтому продемонстрирую полный вариант. Собираем по примеру
    # запросов, указаных в документации.
    # Также, можно передавать дополнительные именованные атрибуты.
    request_data = Node(NS.NS, "RequestData", id="RequestData").value(
        Node(NS.NS, "type").value("GEMSTONE_COLOR_TYPE"),
        Node(NS.NS, "page").value(1),  # Помимо строки, можно передать число.
        Node(NS.NS, "size").value(25),  # Но это значение все равно будет приведено к строке
    )
    # 2) Помещаем эту структуру в обработчик c указанием эндпоинта для запроса. Эндпоинт копируем
    # из документации.
    handler = DMDKHandler("SendGetGlossary", request_data)
    # Для проверки себя, лучше сверяйте собранный документ. До отправки запроса, сделать это можно
    # следующим образом. Сохраним собранное сообщение в файл.
    handler.message.build()
    with open("/app/logs/request.xml", mode="wb") as file:
        file.write(handler.message.to_bytes(pretty_print=True))
    # Далее, вызываем метод process. Под капотом он соберет сообщение, выполнит запрос и вернет
    # ответ в виде словаря. Получить словарь также можно так: handler.response
    response = await handler.process()
    return response
