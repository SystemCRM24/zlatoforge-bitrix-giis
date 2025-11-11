from io import BytesIO
from pathlib import Path

import requests
from lxml import etree  # type:ignore

from src.utils import logger
from src.core import settings


def on_startup():
    """Нужно подтянуть файлик exchange со стороны ГИИС."""
    check_exchange_file('test', settings._giis_test_contour)
    check_exchange_file('work', settings._giis_work_contour)


def check_exchange_file(contour: str, address: str):
    """Проверяет и при необходимости подтягивает exchange3.wsdl файл тестового контура"""
    exchange_file = f"logs/{contour}-exchange3.wsdl"
    if not Path(exchange_file).exists():
        response = requests.get(f"{address}exchange3.wsdl")
        bytes_wsdl = BytesIO(response.content)
        wsdl = etree.parse(bytes_wsdl)
        address_nodes: list = wsdl.xpath('//*[local-name() = "address"]')
        if address_nodes:
            address_node = address_nodes[0]
            address_node.set("location", address)
            wsdl.write(exchange_file)
    logger.info(f"exchange3.wsdl file for {contour=} was setuped.")
