from fastapi import FastAPI, Query
from giis_integration_core._05_receipts._05_02_buyingup_repair._05_02_handler import process_buyingup

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "GIIS Integration Core is running"}

@app.post("/webhook/buyingup_deal")
async def webhook_buyingup_deal(deal_id: int = Query(...)):
    try:
        receipt_id = await process_buyingup(deal_id)
        return {"status": "success", "receipt_id": receipt_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}