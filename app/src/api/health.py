from typing import Literal

from fastapi import APIRouter
from zeep import AsyncClient


router = APIRouter(prefix="")


@router.get("/health", status_code=200)
async def do_health_request(contour: Literal["test", "work"] = "work") -> str:
    """Аналог пинга."""
    return await _do_health_request(contour)


async def _do_health_request(contour: Literal["test", "work"] = "work") -> str:
    """Выполняем запрос."""
    if contour == "work":
        client = AsyncClient("./logs/work-exchange3.wsdl")
    else:
        client = AsyncClient("./logs/test-exchange3.wsdl")
    health_request_data = {"DataForTest": "Hello from my system!", "id": "req-12345-abcde"}
    response = await client.service.Health(
        TestMessage="test",
        OGRN="1234567890123",
        IDTOP="TOP123456789",
        agent="MyPythonApp v1.0",
        RequestData=health_request_data,
    )
    return response.ResponseData.Result
