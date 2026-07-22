from fastapi import FastAPI, HTTPException

# Импортируем наш обработчик
from giis_integration_core._05_receipts._05_02_buyingup_repair._05_02_handler import process_buyingup

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "GIIS Integration Core is running"}

@app.post("/webhook/buyingup_deal")
async def webhook_buyingup_deal(deal_id: int):
    try:
        print(f"📥 Получен вебхук для сделки: {deal_id}")
        receipt_id = await process_buyingup(deal_id)
        
        if receipt_id:
            return {"status": "success", "receipt_id": receipt_id}
        else:
            raise HTTPException(status_code=500, detail="Не удалось создать квитанцию")
            
    except Exception as e:
        print(f"❌ Ошибка в вебхуке: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))