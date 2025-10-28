# pylint: disable=C0116,C0115,C0114
import pytest

from gost_xml_transform import GOSTXMLTransform


@pytest.fixture
def transform_from_str():
    def __wrap__(input_data: str):
        return GOSTXMLTransform.from_string(input_data).to_bytes().decode('utf-8')

    return __wrap__


@pytest.fixture
def transform_from_bytes():
    def __wrap__(input_data: bytes):
        return GOSTXMLTransform.from_bytes(input_data).to_bytes().decode('utf-8')

    return __wrap__
