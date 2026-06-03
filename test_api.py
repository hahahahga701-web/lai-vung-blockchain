import requests
import json
import time

time.sleep(2)
url = 'http://127.0.0.1:8000/api/ai/parse-voice'

# Test data
test_cases = [
    {
        'text': 'lô QL-01 trồng ngày 15 tháng 10 năm 2025, giống quýt hồng Lai Vung, thu hoạch ngày 21 tháng 5 năm 2026, sản lượng 1500 kg, phân bón NPK và phân bón kali, thuốc nano bạc',
        'expected_lot': 'QL-01'
    },
    {
        'text': 'Lô QT-88 giống quýt đường, trồng 05/10/2025, thu hoạch 05/01/2026, sản lượng 2 tấn, dùng phân NPK, thuốc trừ sâu sinh học, loại 1',
        'expected_lot': 'QT-88'
    },
    {
        'text': 'mở lô hàng QL 001 Mã số vùng chống là Lai Vung 0,1 loại giống là Huyết Hồng Lai Vung chất lượng là đạt chuẩn VietGAP ngày trong là ngày 15 tháng 05 năm 2025 ngày thu hoạch là ngày 30 tháng 5 năm 2026 sản lượng 1.2 tấn phân bón là dùng NPK thuốc bảo vệ thực vật cuối cùng là nano bạc',
        'expected_lot': 'QL-001'
    }
]

for i, test in enumerate(test_cases, 1):
    print(f'\n{"="*60}')
    print(f'TEST CASE {i}')
    print(f'{"="*60}')
    print(f'Input: {test["text"]}\n')
    
    try:
        response = requests.post(url, json={'text': test['text']}, timeout=10)
        result = response.json()
        parsed = result.get('parsed_data', {})
        
        print('=== PARSED RESULTS ===')
        print(f'Lot ID:        {parsed.get("lot_id")} {" ✅" if parsed.get("lot_id") == test.get("expected_lot") else " ❌"}')
        print(f'Variety:       {parsed.get("variety")}')
        print(f'Planting Date: {parsed.get("planting_date")}')
        print(f'Harvest Date:  {parsed.get("harvest_date")}')
        print(f'Yield (kg):    {parsed.get("yield_kg")}')
        print(f'Fertilizer:    {parsed.get("fertilizer")}')
        print(f'Pesticide:     {parsed.get("pesticide")}')
        print(f'Quality:       {parsed.get("quality")}')
        print(f'\n=== COMPLETENESS ===')
        print(f'Complete: {result.get("is_complete")}')
        print(f'Missing: {result.get("missing_fields", [])}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

print(f'\n{"="*60}')
print('TEST COMPLETE')
print(f'{"="*60}')
