from fastapi import APIRouter
from zeep import AsyncClient, Client
from zeep.transports import Transport
from lxml import etree


router = APIRouter(prefix="/test", tags=['test'])


@router.get('/health_from_string', status_code=200)
async def get_health_request() -> list:
    """Пример запроса к health из строки"""
    soap_request_str = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="urn://xsd.dmdk.goznak.ru/exchange/3.0">
    <soapenv:Header/>
    <soapenv:Body>
        <ns:HealthRequest>
            <ns:TestMessage>Test</ns:TestMessage>
            <ns:RequestData id="id">
                <ns:DataForTest>Test</ns:DataForTest>
            </ns:RequestData>
        </ns:HealthRequest>
    </soapenv:Body>
    </soapenv:Envelope>'''
    envelope = etree.fromstring(soap_request_str.encode('utf-8'))
    transport = Transport()
    url = "http://0.0.0.0:1500/ws/v3/"
    response = transport.post_xml(
        address=url,
        envelope=envelope,
        headers={
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '"Health"'  # ← если сервер требует SOAPAction, уточни его!
        }
    )
    return etree.tostring(etree.fromstring(response.content), pretty_print=True, encoding='unicode').split('\n')


@router.get('/health_compiled', status_code=200)
async def get_health_request1() -> str:
    """Сборный запрос к Health. 
    На проде будем использовать асинхронный клиент и править а править wsdl будем перед приемом вручную.
    Если все удачно, вернет значение Running.
    """
    client = Client(wsdl="http://0.0.0.0:1500/ws/v3/exchange3.wsdl")
    binding_name = r'{urn://xsd.dmdk.goznak.ru/exchange/3.0}exchangeSoap11'
    new_endpoint = 'http://0.0.0.0:1500/ws/v3'
    service = client.create_service(binding_name, new_endpoint)
    health_request_data = {
        'DataForTest': 'Hello from my system!',
        'id': 'req-12345-abcde'
    }
    response = service.Health(
        TestMessage="test",
        OGRN="1234567890123",
        IDTOP="TOP123456789",
        agent="MyPythonApp v1.0",
        RequestData=health_request_data
    )
    return response.ResponseData.Result
