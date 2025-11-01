import requests
from lxml import etree
from io import BytesIO
from pathlib import Path
from src.utils import logger


def on_startup():
    """Нужно подтянуть файлик exchange со стороны ГИИС."""
    exchange_file = 'logs/exchange3.wsdl'
    if not Path(exchange_file).exists():
        response = requests.get('http://0.0.0.0:1500/ws/v3/exchange3.wsdl')
        bytes_wsdl = BytesIO(response.content)
        wsdl = etree.parse(bytes_wsdl)
        address_nodes: list = wsdl.xpath('//*[local-name() = "address"]')
        if address_nodes:
            address_node = address_nodes[0]
            address_node.set('location', 'http://0.0.0.0:1500/ws/v3')
            wsdl.write('logs/exchange3.wsdl')
    logger.info('exchange3.wsdl file was downloaded and edited.')
