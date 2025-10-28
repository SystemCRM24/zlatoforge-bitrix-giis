"""
Общиие тест-кейсы из:
Методические рекомендации по работе со СМЭВ версия 3.5.0.1
"""
# pylint: disable=C0116,C0115,C0114
import json


def test_all(transform_from_str):
    with open('tests/data.json', 'r') as fp:
        json_data = json.load(fp)

    for (in_, output) in json_data:
        assert transform_from_str(in_) == output
