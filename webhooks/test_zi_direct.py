import sys
import asyncio
import traceback

sys.path.insert(0, '/app/my_new_app')
from services.prepack_service import create_prepack_in_giis

async def main():
    print("🚀 Запуск прямого теста создания ЗИ в ГИИС...")
    try:
        res = await create_prepack_in_giis(
            receipt_id_giis="P-02-000005581-26",
            name="Тестовое изделие ЗИ",
            quantity=1,
            weight_g=3.50,
            hallmark="58500",
            hcm_g=0.50,
            category="JT_RING",
            batch_type="PREPACK_PRODUCT",
            metal_type="DM_GOLD",
            okpd2="32.12.13.110",
            description="Прямой тест из консоли",
            contour="test"
        )
        print(f"✅ УСПЕХ! Ответ ГИИС: {res}")
    except Exception as e:
        print(f"❌ ОШИБКА: {type(e).__name__}: {e}")
        print(f"📋 Детали ошибки:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())