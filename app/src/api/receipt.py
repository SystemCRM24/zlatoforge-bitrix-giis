import asyncio

from fastapi import APIRouter, Query

from src.schemas.queries import ManufacturingReceiptQuerySchema, ReceiptQuerySchema
from src.services.jewelry_manufacturing import (
    create_production_receipt as _create_production_receipt,
)
from src.services.scrap_receipt import create_scrap_receipt as _create_scrap_receipt


router = APIRouter(prefix="")


@router.post("/create_scrap_receipt", status_code=201)
async def create_scrap_receipt(q: ReceiptQuerySchema = Query()) -> str:
    """Создание квитанции на скупку лома на основе данных битрикса клиента."""
    coro = _create_scrap_receipt(q)
    asyncio.create_task(coro)
    return "Task created"


@router.post("/create_manufacturing_receipt", status_code=201)
async def create_production_receipt(q: ManufacturingReceiptQuerySchema = Query()) -> str:
    """Создание квитанции на изготовление ювелирного изделия."""
    coro = _create_production_receipt(q)
    asyncio.create_task(coro)
    return "Task created"
