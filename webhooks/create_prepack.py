import sys, requests
sys.path.insert(0, '/app/my_new_app')
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from services.prepack_service import create_prepack_in_giis

app = FastAPI()
# Ваш новый ID пользователя (1)
B = "https://zlatokuznica.bitrix24.ru/rest/1/ak5wbpxa2hoyrt21/"

def get_b24(i):
    r = requests.post(f"{B}crm.item.get.json", json={"entityTypeId": 157, "id": int(i)}, timeout=10).json()
    return r.get("result", {}).get("item", {}).get("fields", {})

def upd_b24(i, f):
    try: requests.post(f"{B}crm.item.update.json", json={"entityTypeId": 157, "id": int(i), "fields": f}, timeout=5)
    except: pass

@app.api_route("/api/create_prepack", methods=["GET", "POST"])
async def handle_prepack(receipt_id: str):
    try:
        u = get_b24(receipt_id)
        
        # ТОЧНЫЕ коды полей из карточки
        hall = str(u.get("ufCrm16ProbaGiisDmdk") or u.get("ufCrm16_1706010251505") or "585").strip()
        if len(hall) == 3 and hall.isdigit(): hall += "00"
        
        weight = float(u.get("ufCrm16_1731161962") or 0)
        hcm = float(u.get("ufCrm16_1706010460768") or 0)
        qty = int(float(u.get("ufCrm16_1706858262577") or 1))
        okpd = str(u.get("ufCrm_16_OKPD2") or u.get("ufCrm16_1736183115943") or "32.12.13.110").strip()
        kvit = str(u.get("ufCrm16KvitantsiaGiisDmdk") or "").strip()
        name = str(u.get("TITLE") or "Заготовка").strip()
        category = str(u.get("ufCrm16GiisCategory") or "JT_RING").strip()
        metal = str(u.get("ufCrm16MetalType") or "DM_GOLD").strip()
        
        desc = str(u.get("ufCrm16Opisanie") or "").strip()
        if kvit and kvit not in desc:
            desc = f"{desc} (Квит: {kvit})".strip() if desc else f"Создано из квитанции {kvit}"

        print(f"✅ DATA: hall={hall}, w={weight}, hcm={hcm}, okpd={okpd}, kvit={kvit}")
        print("⚠️ ОТПРАВКА В ТЕСТОВЫЙ КОНТУР (contour='test')")
        
        # Отправка в ГИИС ДМДК
        res = await create_prepack_in_giis(
            receipt_id_giis=kvit, name=name, quantity=qty, weight_g=weight,
            hallmark=hall, hcm_g=hcm, category=category, batch_type="PREPACK_PRODUCT",
            metal_type=metal, okpd2=okpd, description=desc, contour="test"
        )
        
        print(f"✅ GIIS RESPONSE: {res}")
        
        # Обновляем поля в Битрикс24
        upd_b24(receipt_id, {
            "ufCrm16MessageIdGiis": res.get("messageId", ""), 
            "ufCrm16GiisStatus": res.get("status", ""), 
            "ufCrm16_1736183849955": res.get("uin", "")
        })
        return JSONResponse(content={"success": True, "giis": res})
    except Exception as e:
        print(f"❌ ERROR: {e}")
        upd_b24(receipt_id, {"ufCrm16GiisStatus": "ERROR", "ufCrm16MessageIdGiis": str(e)})
        raise HTTPException(status_code=500, detail=str(e))