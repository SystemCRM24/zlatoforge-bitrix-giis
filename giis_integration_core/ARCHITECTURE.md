# Архитектура приложения Zlatoforge GIIS DMDK

## Общая схема

    БИТРИКС24 → api/ → services/ → core/ → stunnel → ГИИС ДМДК

## Структура папок

- core/ — Ядро (от ООО СПЕЦСИСТЕМА): подпись, XML, транспорт
- services/ — Бизнес-логика (наша): ремонт, изготовление, скупка
- api/ — REST API для Битрикс24
- config/ — Настройки
- logs/ — Логи работы

## Поток данных

1. Битрикс24 → вебхук → api/routes.py
2. api/ → services/ (бизнес-логика)
3. services/ → core/ (XML + подпись)
4. core/ → stunnel → ГИИС ДМДК
5. ГИИС → ответ → services/ → Битрикс24

## Как добавить новую операцию

1. Создать файл в services/
2. Использовать core/xml_message.py, core/cypher.py, core/handler.py
3. Добавить эндпоинт в api/routes.py
