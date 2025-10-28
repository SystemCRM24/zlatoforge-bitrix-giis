"""
тест-кейсы для поверики следующих правил:
- После применения правил из пунктов 1 и 20, если даже у элемента нет дочерних узлов,
  элемент не может быть представлен в виде empty element tag
  (http://www.w3.org/TR/2008/REC-xml-20081126/#sec-starttags, правило [44]),
  а должен быть преобразован в пару start-tag + end-tag.
- Если текстовый узел содержит только пробельные символы
  (код символа меньше или равен '\u0020'), этот текстовый узел вырезается.
- Удалить namespace prefix, которые на текущем уровне объявляются, но не используются.
- Проверить, что namespace текущего элемента объявлен либо выше по дереву, либо в текущем элементе.
  Если не объявлен, объявить в текущем элементе.
- Namespace prefix элементов и атрибутов должны быть заменены на автоматически сгенерированные.
  Сгенерированный префикс состоит из литерала «ns», и порядкового номера сгенерированного префикса
  в рамках обрабатываемого XML-фрагмента, начиная с единицы.
  При генерации префиксов должно устраняться их дублирование.
"""


# pylint: disable=C0116,C0115,C0114


def test_self_close_tag(transform_from_str):
    assert transform_from_str("<tag/>") == '<tag></tag>'


def test_rm_empty_text(transform_from_str):
    assert transform_from_str("<tag>        </tag>") == '<tag></tag>'


def test_pass_text(transform_from_str):
    assert transform_from_str("<tag>  text  </tag>") == '<tag>  text  </tag>'


def test_rm_unused_namespace(transform_from_str):
    assert transform_from_str('<tag  xmlns:myns="urn://x" />') == '<tag></tag>'


def test_rename_namespace(transform_from_str):
    assert transform_from_str(
        '<myns:tag xmlns:myns="urn://x" />'
    ) == '<ns1:tag xmlns:ns1="urn://x"></ns1:tag>'


def test_children_namespace(transform_from_str):
    assert transform_from_str(
        '<myns:tag xmlns:myns="urn://x"  xmlns:myns2="urn://x1">'
        '<myns2:tag2/>'
        '</myns:tag>'
    ) == '<ns1:tag xmlns:ns1="urn://x"><ns2:tag2 xmlns:ns2="urn://x1"></ns2:tag2></ns1:tag>'


def test_children_namespace_2(transform_from_str):
    assert transform_from_str(
        '<myns:tag xmlns:myns="urn://x"  xmlns:myns2="urn://x1">'
        '<myns2:tag2/>'
        '<myns2:tag2/>'
        '</myns:tag>'
    ) == (
        '<ns1:tag xmlns:ns1="urn://x">'
        '<ns2:tag2 xmlns:ns2="urn://x1"></ns2:tag2>'
        '<ns3:tag2 xmlns:ns3="urn://x1"></ns3:tag2>'
        '</ns1:tag>'
    )
