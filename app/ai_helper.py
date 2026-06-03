import re
import os
import sys
import json
from datetime import datetime
from openai import AsyncOpenAI

def safe_print(*args, **kwargs):
    """Print helper chống crash UnicodeEncodeError trên Windows console (cp1258)."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode với errors='replace' rồi in ra stdout
        text = " ".join(str(a) for a in args)
        sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
        sys.stdout.buffer.write(b'\n')
        sys.stdout.buffer.flush()

# Khởi tạo client kết nối đến Cerebras
CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY")
if not CEREBRAS_API_KEY:
    # Sử dụng key hoạt động từ Chatbot làm fallback mặc định
    CEREBRAS_API_KEY = "csk-62dwtj8mphpwydyf9x6nwnv4ep2fdw8m296k29fnykhknt9n"
    print("[INFO] CEREBRAS_API_KEY not found in environment variables. Falling back to chatbot key.")

client = AsyncOpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=CEREBRAS_API_KEY
)

def normalize_vietnamese_text(text: str) -> str:
    """
    Tiền xử lý và chuẩn hóa chuỗi đầu vào tiếng Việt nhằm khắc phục các lỗi STT phổ biến
    và định dạng lại các mã số nông nghiệp (Lot ID, Planting Area Code).
    """
    if not text:
        return ""
    
    t_lower = text.lower()
    
    # 1. Sửa lỗi chính tả/phát âm do STT nhận diện sai
    t_lower = t_lower.replace("vùng chống", "vùng trồng")
    t_lower = t_lower.replace("vùng chông", "vùng trồng")
    t_lower = t_lower.replace("vung chong", "vung trong")
    t_lower = t_lower.replace("ngày trong", "ngày trồng")
    t_lower = t_lower.replace("ngày chông", "ngày trồng")
    t_lower = t_lower.replace("ngày tròng", "ngày trồng")
    
    # 2. Chuẩn hóa số/mã có chứa dấu phẩy hoặc chấm được đọc dưới dạng mã vùng trồng (ví dụ: "0,1" hoặc "0.1" -> "01")
    t_lower = re.sub(r'\blai\s+vung\s+0\s*[,.]\s*1\b', 'lai vung 01', t_lower)
    t_lower = re.sub(r'\bvung\s+lai\s+0\s*[,.]\s*1\b', 'vung lai 01', t_lower)
    # Tổng quát hóa cho bất kỳ số nào có dạng "0,x" hoặc "0.x" đi sau từ "vùng trồng", "vùng", "lô"
    t_lower = re.sub(r'(vùng\s+trồng|vùng|lô|mã)\s+([a-z\s]+)\s+0\s*[,.]\s*(\d+)', r'\1 \2 0\3', t_lower)
    
    # 3. Chuẩn hóa các cụm mã: chữ + khoảng trắng + số (ví dụ: ql 001 -> ql-001)
    t_lower = re.sub(r'\b(ql|qt|lot)\s*[-]?\s*(\d+)\b', r'\1-\2', t_lower)
    
    # 4. Chuẩn hóa mã vùng trồng: vung lai 001 -> vung-lai-001, lai vung 01 -> lai-vung-01
    t_lower = re.sub(r'\bvung\s+lai\s*[-]?\s*(\d+)\b', r'vung-lai-\1', t_lower)
    t_lower = re.sub(r'\blai\s+vung\s*[-]?\s*(\d+)\b', r'lai-vung-\1', t_lower)
    t_lower = re.sub(r'\bvung-lai-vung\s*[-]?\s*(\d+)\b', r'vung-lai-vung-\1', t_lower)
    
    return t_lower

def clean_filler_words(val: str) -> str:
    """
    Loại bỏ các từ nối thừa ở đầu hoặc cuối chuỗi khi nông dân phát biểu tự do
    để tránh việc điền biểu mẫu bị dính từ ngữ cảnh thừa.
    """
    if not val:
        return ""
    
    val_clean = val.strip()
    
    # Xóa từ nối thừa ở đầu chuỗi (không phân biệt hoa thường)
    pattern_start = r'^(?:là\s+dùng|dùng\s+là|cuối\s+cùng\s+là|loại\s+giống\s+là|giống\s+là|ngày\s+là|là|dùng|bón|phun|xịt|sử\s+dụng|đã\s+dùng|chỉ\s+là|nhật\s+ký|cụ\s+thể\s+là)\s+'
    val_clean = re.sub(pattern_start, '', val_clean, flags=re.IGNORECASE)
    
    # Xóa từ nối thừa ở cuối chuỗi
    pattern_end = r'\s+(?:là|dùng|bón|phun|xịt|sử\s+dụng|đã\s+dùng|cuối\s+cùng|nhật\s+ký|cụ\s+thể\s+là)$'
    val_clean = re.sub(pattern_end, '', val_clean, flags=re.IGNORECASE)
    
    # Xóa các ký tự phân tách thừa ở đầu/cuối chuỗi
    val_clean = re.sub(r'^[:\-\s,]+', '', val_clean)
    val_clean = re.sub(r'[:\-\s,]+$', '', val_clean)
    
    return val_clean.strip()

# Prompt mẫu phục vụ hiển thị trên giao diện (cho người dùng hiểu cách LLM hoạt động ở môi trường Production)
LLM_PROMPT_TEMPLATE = """
Bạn là một trợ lý AI chuyên nghiệp phục vụ cho hợp tác xã nông nghiệp Quýt Hồng Lai Vung.
Nhiệm vụ của bạn là phân tích đoạn văn bản thô được dịch từ giọng nói của nông dân sang cấu trúc JSON chuẩn để lưu trữ hệ thống.

Văn bản thô: "{text}"

Yêu cầu đầu ra JSON:
{
  "lot_id": "Mã lô (ví dụ: QL-01, QT-12)",
  "planting_area_code": "Mã số vùng trồng (ví dụ: VUNG-LAI-001)",
  "variety": "Loại giống quýt",
  "planting_date": "Ngày trồng (định dạng YYYY-MM-DD)",
  "fertilizer": "Các loại phân bón đã dùng",
  "pesticide": "Các loại thuốc BVTV đã dùng",
  "last_spray_date": "Ngày phun thuốc cuối cùng (định dạng YYYY-MM-DD, hoặc null nếu không có)",
  "harvest_date": "Ngày thu hoạch (định dạng YYYY-MM-DD)",
  "yield_kg": "Sản lượng thu hoạch tính bằng kg (số thực)",
  "brix_value": "Chỉ số độ ngọt Brix (số thực, hoặc null nếu không có)",
  "quality": "Đánh giá chất lượng (loại 1, loại 2, xuất khẩu,...)"
}
Lưu ý: Chỉ trả về JSON thuần túy, không có thẻ ```json hay giải thích thêm.
"""

CEREBRAS_SYSTEM_PROMPT = """
Bạn là một trợ lý AI chuyên nghiệp phục vụ cho hợp tác xã nông nghiệp Quýt Hồng Lai Vung.
Nhiệm vụ của bạn là phân tích đoạn văn bản thô được dịch từ giọng nói của nông dân sang cấu trúc JSON chuẩn để lưu trữ hệ thống.

Cấu trúc JSON bắt buộc phải trả về:
{
  "lot_id": "Mã lô (ví dụ: QL-01, QT-88, hoặc null nếu không tìm thấy)",
  "planting_area_code": "Mã số vùng trồng (ví dụ: VUNG-LAI-001, hoặc null nếu không tìm thấy)",
  "variety": "Loại giống quýt (ví dụ: Quýt Hồng Lai Vung, Quýt Đường, hoặc null nếu không đề cập)",
  "planting_date": "Ngày trồng (định dạng YYYY-MM-DD, hoặc null nếu không có thông tin)",
  "fertilizer": "Các loại phân bón đã dùng (hoặc null)",
  "pesticide": "Các loại thuốc BVTV đã dùng (hoặc null)",
  "last_spray_date": "Ngày phun thuốc cuối cùng (định dạng YYYY-MM-DD, hoặc null)",
  "harvest_date": "Ngày thu hoạch (định dạng YYYY-MM-DD, hoặc null)",
  "yield_kg": "Sản lượng thu hoạch tính bằng kg (số thực, hoặc null)",
  "brix_value": "Chỉ số độ ngọt Brix (số thực, hoặc null)",
  "quality": "Đánh giá chất lượng (ví dụ: Loại 1 (Cao cấp), Loại 2, Đạt chuẩn Xuất khẩu, Đạt chuẩn VietGAP, hoặc null)",
  "is_complete": boolean (true nếu đủ mã lô hàng lot_id, giống variety, mã vùng trồng planting_area_code, ngày thu hoạch harvest_date và sản lượng yield_kg; ngược lại false),
  "missing_fields": ["danh sách tên tiếng Việt của các trường bắt buộc còn thiếu trong các trường: Mã lô hàng, Mã số vùng trồng, Loại giống, Ngày trồng, Ngày thu hoạch, Nhật ký phân bón, Thuốc bảo vệ thực vật, Sản lượng, Đánh giá chất lượng"],
  "feedback_message": "Lời nhắn tiếng Việt cực kỳ thân thiện, ghi nhận các trường đã bóc tách được và chỉ ra rõ các trường còn thiếu để nông dân bổ sung giọng nói."
}

Yêu cầu cực kỳ quan trọng:
1. Chỉ trả về DUY NHẤT một chuỗi JSON hợp lệ. Không giải thích gì thêm, không bọc trong thẻ ```json.
2. Cố gắng suy luận ngày tháng năm. Nếu nông dân nói "ngày mười lăm tháng năm" thì mặc định năm là năm hiện tại (2026). Nếu nói "năm ngoái" thì là năm trước đó (2025).
3. Đổi các đơn vị sản lượng (ví dụ: 1.5 tấn = 1500, 3 tạ = 300) về đơn vị kg (số thực).
4. Phân tích ngữ cảnh kỹ để điền đúng các trường.
5. Tuyệt đối KHÔNG giữ lại các từ nối thừa ở đầu hoặc cuối các giá trị chuỗi (như "là", "ngày là", "cuối cùng là", "là dùng", "dùng", "bón", "loại giống là", v.v.). Giá trị của các trường trong JSON trả về phải được làm sạch và chuẩn hóa hoàn toàn (ví dụ: "fertilizer": "NPK hữu cơ" thay vì "Là dùng NPK hữu cơ", "variety": "Quýt Hồng Lai Vung" thay vì "Là Huyết Hồng Lai Vung").
6. Chuẩn hóa mã lô hàng (lot_id) viết liền, viết hoa và có dấu gạch ngang chuẩn (ví dụ: QL-01, QT-88). Chuẩn hóa mã vùng trồng (planting_area_code) viết liền, viết hoa và có dấu gạch ngang (ví dụ: LAI-VUNG-01, VUNG-LAI-001). Nếu người dùng nói "QL 01" hoặc "QL 001", hãy chuyển thành "QL-01" hoặc "QL-001". Nếu nói "Lai Vung 0,1" hoặc "vùng Lai Vung 0.1", hãy chuyển thành "LAI-VUNG-01".
"""

async def parse_vietnamese_speech(text: str) -> dict:
    """
    Phân tích đoạn text tiếng Việt sử dụng Cerebras Llama 3.1-70b thực tế.
    Nếu thất bại, tự động chuyển sang phân tích Regex dự phòng (fallback)
    để đảm bảo hệ thống không bị crash.
    """
    # Tiền xử lý chuẩn hóa chuỗi đầu vào trước
    normalized_text = normalize_vietnamese_text(text)
    
    try:
        # Kiểm tra nếu API key không hợp lệ, bỏ qua gọi API
        if CEREBRAS_API_KEY == "placeholder-key-use-env-var" or not CEREBRAS_API_KEY:
            raise Exception("CEREBRAS_API_KEY is not configured. Using fallback parsing.")
        
        # Gọi API Cerebras thực tế
        # Thử gọi model "gpt-oss-120b" trước, nếu bị lỗi model thì tự động chuyển sang model chuẩn "llama3.3-70b"
        try:
            response = await client.chat.completions.create(
                model="gpt-oss-120b",
                messages=[
                    {"role": "system", "content": CEREBRAS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Trích xuất dữ liệu từ đoạn thu âm sau: '{normalized_text}'"}
                ],
                temperature=0.1
            )
        except Exception as api_err:
            print(f"[WARNING] API call with model gpt-oss-120b failed: {api_err}. Trying llama3.3-70b fallback...")
            response = await client.chat.completions.create(
                model="llama3.3-70b",
                messages=[
                    {"role": "system", "content": CEREBRAS_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Trích xuất dữ liệu từ đoạn thu âm sau: '{normalized_text}'"}
                ],
                temperature=0.1
            )
        
        raw_content = response.choices[0].message.content
        safe_print(f"[DEBUG] Raw Cerebras response: {raw_content[:200]}...")
        
        # Xóa ```json wrapper nếu LLM trả về
        raw_content = raw_content.strip()
        if raw_content.startswith("```json"):
            raw_content = raw_content.replace("```json", "", 1).replace("```", "", 1).strip()
        elif raw_content.startswith("```"):
            raw_content = raw_content.replace("```", "", 2).strip()
        
        try:
            extracted_data = json.loads(raw_content)
        except json.JSONDecodeError as json_err:
            safe_print(f"[ERROR] JSON parsing failed: {json_err}")
            safe_print(f"[ERROR] Raw content was: {raw_content[:500]}")
            raise Exception(f"Invalid JSON response from Cerebras API: {str(json_err)}")
        
        # Đảm bảo các trường của database luôn tồn tại (nếu thiếu thì đặt mặc định hợp lý)
        for field in ["lot_id", "variety", "planting_area_code", "planting_date", "last_spray_date", "fertilizer", "pesticide", "harvest_date", "yield_kg", "quality", "brix_value"]:
            if field not in extracted_data:
                extracted_data[field] = None
        
        # Thêm các trường chẩn đoán nếu LLM không tạo ra hoặc bị thiếu
        if "is_complete" not in extracted_data:
            extracted_data["is_complete"] = True if (
                extracted_data.get("lot_id") and 
                extracted_data.get("planting_area_code") and
                extracted_data.get("variety") and
                extracted_data.get("planting_date") and
                extracted_data.get("harvest_date") and
                extracted_data.get("yield_kg") and
                extracted_data.get("fertilizer") and
                extracted_data.get("pesticide") and
                extracted_data.get("quality")
            ) else False
        if "missing_fields" not in extracted_data:
            extracted_data["missing_fields"] = []
        if "feedback_message" not in extracted_data:
            extracted_data["feedback_message"] = "Đã tiếp nhận nhật ký của bạn thành công!"
            
        safe_print("[INFO] Successfully parsed speech with Cerebras AI")
        return extracted_data

    except Exception as e:
        safe_print(f"[ERROR] Cerebras API call failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        safe_print(f"[INFO] Falling back to regex-based parsing...")
        # Chạy logic bóc tách regex dự phòng (truyền chuỗi đã chuẩn hóa)
        fallback_data = parse_vietnamese_speech_regex(normalized_text)
        
        # Định nghĩa các trường bổ sung cho fallback để frontend không bị lỗi
        missing_fields = []
        if not fallback_data.get("lot_id"): missing_fields.append("Mã lô hàng")
        if not fallback_data.get("planting_area_code"): missing_fields.append("Mã số vùng trồng")
        if not fallback_data.get("variety"): missing_fields.append("Loại giống")
        if not fallback_data.get("planting_date"): missing_fields.append("Ngày trồng")
        if not fallback_data.get("harvest_date"): missing_fields.append("Ngày thu hoạch")
        if not fallback_data.get("fertilizer"): missing_fields.append("Nhật ký phân bón")
        if not fallback_data.get("pesticide"): missing_fields.append("Thuốc bảo vệ thực vật")
        if not fallback_data.get("yield_kg"): missing_fields.append("Sản lượng")
        if not fallback_data.get("quality"): missing_fields.append("Đánh giá chất lượng")
        
        is_complete = len(missing_fields) == 0
        feedback_message = (
            "Chào bác nông dân! Tôi đã lưu nhật ký của bác bằng hệ thống dự phòng. "
            "Dữ liệu có vẻ đã đầy đủ!" if is_complete else
            f"Chào bác! Hệ thống dự phòng đã ghi nhận một phần thông tin, bác vui lòng bổ sung thêm: {', '.join(missing_fields)}."
        )
        
        print(f"[INFO] Using regex fallback - is_complete: {is_complete}")
        fallback_result = {
            **fallback_data,
            "is_complete": is_complete,
            "missing_fields": missing_fields,
            "feedback_message": feedback_message,
            "is_fallback": True
        }
        return fallback_result

def parse_vietnamese_speech_regex(text: str) -> dict:
    """
    Phân tích đoạn text tiếng Việt (mô phỏng LLM bóc tách văn bản nông nghiệp)
    thành cấu trúc JSON chuẩn cho thông tin trồng trọt. (Cơ chế fallback bằng Regex)
    
    Cải tiến: 
    - Mã lô phải match pattern chuẩn (QL-01, QT-88, v.v.)
    - Sản lượng phải tìm gần keyword "sản lượng"
    - Các trường được tách riêng biệt theo context
    """
    result = {
        "lot_id": None,
        "variety": None,
        "planting_area_code": None,
        "planting_date": None,
        "last_spray_date": None,
        "fertilizer": None,
        "pesticide": None,
        "harvest_date": None,
        "yield_kg": None,
        "quality": None,
        "brix_value": None
    }
    
    text_lower = text.lower()
    text_original = text  # Giữ nguyên để extract chuỗi có dấu
    
    # ===== 1. TRÍCH XUẤT MÃ LÔ (LOT ID) =====
    # Pattern: lô [mã] QL-01, lô QT-88, mã lô QL01, v.v.
    # Phải match: chữ cái (1-3 ký tự) + dash/không + số (1-4 ký tự)
    
    # Tìm dạng: (lô|mã) [lô/hàng/lô hàng] XXXX-NN hoặc XXXXNN
    lot_pattern1 = re.search(r'(?:lô|mã)\s*(?:lô|hàng|lô\s+hàng)?\s*(?:là)?\s*([a-z]{1,3}\s*[-]?\s*\d{1,4})\b', text_lower)
    if lot_pattern1:
        candidate = lot_pattern1.group(1).replace(" ", "").upper()
        if "-" not in candidate:
            candidate = re.sub(r'^([A-Z]+)(\d+)$', r'\1-\2', candidate)
        result["lot_id"] = candidate
    else:
        # Tìm dạng tiền tố: QL-01, QT-88, v.v. (không cần keyword)
        lot_pattern2 = re.search(r'\b([a-z]{2,3}\s*[-]?\s*\d{1,4})\b', text_lower)
        if lot_pattern2:
            candidate = lot_pattern2.group(1).replace(" ", "").upper()
            if "-" not in candidate:
                candidate = re.sub(r'^([A-Z]+)(\d+)$', r'\1-\2', candidate)
            # Validate: phải có chữ + số, không phải toàn số hoặc toàn chữ
            if re.match(r'[A-Z]+-?\d', candidate):
                result["lot_id"] = candidate
    
    # Nếu vẫn không tìm được, để None (sẽ nhắc người dùng bổ sung)
    if not result["lot_id"]:
        result["lot_id"] = None

    # ===== 1.5. TRÍCH XUẤT MÃ SỐ VÙNG TRỒNG (PLANTING AREA CODE) =====
    # Pattern: vùng trồng [mã] VUNG-LAI-001, vùng VUNG-02, v.v.
    # Vùng trồng thường có dạng VUNG-LAI-001 hoặc LAI-VUNG-01 hoặc VUNG01
    area_pattern1 = re.search(r'(?:vùng\s+trồng|vùng|mã\s+vùng)\s*(?:là|[:\-]|vùng)?\s*([a-z0-9\-]+)\b', text_lower)
    if area_pattern1:
        result["planting_area_code"] = area_pattern1.group(1).strip().upper()
    else:
        # Tìm bất kỳ pattern có dạng VUNG-... hoặc LAI-VUNG-...
        area_pattern2 = re.search(r'\b(vung[-a-z0-9]+|lai-vung[-a-z0-9]+)\b', text_lower)
        if area_pattern2:
            result["planting_area_code"] = area_pattern2.group(1).upper()

    # ===== 2. LOẠI GIỐNG QUÝT =====
    if "quýt hồng" in text_lower or "quýt đặc sản" in text_lower or "quýt lai vung" in text_lower or "huyết hồng" in text_lower:
        result["variety"] = "Quýt Hồng Lai Vung"
    elif "quýt đường" in text_lower:
        result["variety"] = "Quýt Đường"
    elif "giống" in text_lower:
        # Trích xuất cụm sau từ "giống" và dừng trước các trường khác
        giong_match = re.search(
            r'giống\s+(?:là|loại)?\s*([^,\.\n]+?)(?:\s+trồng|\s+ngày|\s+chất\s+lượng|\s+đạt|\s+sản\s+lượng|\s+phân|\s+thuốc|\s+thu\s+hoạch|\s+loại|,|\.|$)', 
            text_lower
        )
        if giong_match:
            result["variety"] = clean_filler_words(giong_match.group(1)).strip().title()

    # ===== 3. NGÀY TRỒNG, NGÀY THU HOẠCH VÀ NGÀY PHUN THUỐC CUỐI =====
    # Tìm tất cả ngày dạng: ngày DD tháng MM [năm YYYY] hoặc DD/MM/YYYY
    dates_with_context = {}  # {"trồng": "2025-10-15", "thu_hoạch": "2026-05-21", "phun_cuối": "2026-05-05"}
    
    # Pattern 1: ngày 15 tháng 10 năm 2025 hoặc ngày 15 tháng 10
    date_pattern1 = r'(?:ngày\s+)?(\d{1,2})\s+(?:tháng|/|-)\s*(\d{1,2})(?:\s+(?:năm|/)?\s*(\d{4}))?'
    # Pattern 2: 05/10/2025 hoặc 05-10-2025 (explicit format)
    date_pattern2 = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})'
    
    all_dates = []
    
    # Collect dates from pattern 1
    for match in re.finditer(date_pattern1, text_lower):
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else datetime.now().year
        all_dates.append((day, month, year, match.start()))
    
    # Collect dates from pattern 2
    for match in re.finditer(date_pattern2, text_lower):
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        all_dates.append((day, month, year, match.start()))
    
    # Sort by position in text to maintain order
    all_dates.sort(key=lambda x: x[3])
    
    # Remove duplicates (same date at same position)
    seen_dates = set()
    unique_dates = []
    for d, m, y, pos in all_dates:
        key = (d, m, y)
        if key not in seen_dates:
            seen_dates.add(key)
            unique_dates.append((d, m, y, pos))
    
    # Process each date
    for day, month, year, pos in unique_dates:
        try:
            date_obj = datetime(year, month, day)
            date_str = date_obj.strftime("%Y-%m-%d")
            
            # Xác định context: trồng, thu hoạch hay phun thuốc?
            context_start = max(0, pos - 50)
            context_text = text_lower[context_start:pos + 30]
            
            if "trồng" in context_text and "trồng" not in dates_with_context:
                dates_with_context["trồng"] = date_str
            elif "thu hoạch" in context_text and "thu_hoạch" not in dates_with_context:
                dates_with_context["thu_hoạch"] = date_str
            elif ("phun" in context_text or "xịt" in context_text or "bvtv" in context_text) and "phun_cuối" not in dates_with_context:
                dates_with_context["phun_cuối"] = date_str
            elif "trồng" not in dates_with_context and "thu_hoạch" not in dates_with_context:
                # Mặc định ngày đầu là ngày trồng
                dates_with_context["trồng"] = date_str
        except ValueError:
            # Ngày không hợp lệ (ví dụ: 31/02)
            pass
    
    result["planting_date"] = dates_with_context.get("trồng")
    result["harvest_date"] = dates_with_context.get("thu_hoạch")
    result["last_spray_date"] = dates_with_context.get("phun_cuối")

    # ===== 4. PHÂN BÓN =====
    # Tìm cụm: "phân bón [loại]" hoặc "[loại] phân bón"
    fertilizer_section_match = re.search(
        r'(?:nhật ký\s+)?phân bón\s*(?:là|gồm|dùng|bón|:|\-)?\s*([^,\.]+?)(?:\s+thuốc|\s+sản lượng|\s+ngày|\s+loại|\s+đạt|\s+thu\s+hoạch|,|\.|$)',
        text_lower
    )
    if fertilizer_section_match:
        cleaned_val = clean_filler_words(fertilizer_section_match.group(1))
        if cleaned_val:
            result["fertilizer"] = cleaned_val.strip().title()
            
    if not result["fertilizer"]:
        # Fallback: tìm keyword phân bón
        fertilizer_keywords = [
            ("npk", "Phân bón NPK"),
            ("ure", "Phân bón Ure"),
            ("kali", "Phân bón Kali"),
            ("phân hữu cơ", "Phân bón hữu cơ"),
            ("phân chuồng", "Phân bón chuồng"),
        ]
        for keyword, label in fertilizer_keywords:
            if keyword in text_lower:
                result["fertilizer"] = label
                break
        
        # Nếu vẫn không tìm được nhưng có "bón"
        if not result["fertilizer"] and ("bón" in text_lower or "phân bón" in text_lower):
            result["fertilizer"] = "Phân bón hữu cơ sinh học"

    # ===== 5. THUỐC BẢO VỆ THỰC VẬT =====
    # Tìm cụm: "thuốc [loại]" hoặc "[loại] thuốc"
    pesticide_section_match = re.search(
        r'(?:nhật ký\s+)?(?:thuốc bảo vệ thực vật|thuốc|bvtv)\s*(?:là|gồm|dùng|phun|xịt|:|\-)?\s*([^,\.]+?)(?:\s+sản lượng|\s+ngày|\s+loại|\s+đạt|\s+thu\s+hoạch|,|\.|$)',
        text_lower
    )
    if pesticide_section_match:
        cleaned_val = clean_filler_words(pesticide_section_match.group(1))
        if cleaned_val:
            result["pesticide"] = cleaned_val.strip().title()
            
    if not result["pesticide"]:
        # Fallback: tìm keyword
        pesticide_keywords = [
            ("nano bạc", "Chế phẩm Nano Bạc"),
            ("thuốc sâu", "Thuốc trừ sâu"),
            ("chế phẩm sinh học", "Thuốc BVTV sinh học"),
            ("trừ sâu", "Thuốc trừ sâu hữu cơ"),
        ]
        for keyword, label in pesticide_keywords:
            if keyword in text_lower:
                result["pesticide"] = label
                break
        
        # Nếu vẫn không tìm được nhưng có "phun" hoặc "xịt"
        if not result["pesticide"] and ("phun" in text_lower or "xịt" in text_lower):
            result["pesticide"] = "Chế phẩm bảo vệ thực vật hữu cơ"

    # ===== 6. SẢN LƯỢNG (YIELD) =====
    # Ưu tiên: tìm "sản lượng XXX [đơn vị]"
    yield_pattern1 = re.search(
        r'sản lượng\s*[:\-]?\s*(\d+(?:[\.,]\d+)?)\s*(tấn|tạ|kg|ký)\b',
        text_lower
    )
    if yield_pattern1:
        val = float(yield_pattern1.group(1).replace(',', '.'))
        unit = yield_pattern1.group(2)
        if unit == "tấn":
            result["yield_kg"] = val * 1000
        elif unit == "tạ":
            result["yield_kg"] = val * 100
        else:  # kg hoặc ký
            result["yield_kg"] = val
    else:
        # Tìm kiếm thứ cấp: số + đơn vị nông nghiệp (không bắt từ ngày)
        # Tách chuỗi thành các phần
        for part in re.split(r'[,\.;\n]', text_lower):
            if "sản lượng" in part or "thu hoạch" in part:
                yield_match = re.search(r'(\d+(?:\.\d+)?)\s*(tấn|tạ|kg|ký)\b', part)
                if yield_match:
                    val = float(yield_match.group(1))
                    unit = yield_match.group(2)
                    if unit == "tấn":
                        result["yield_kg"] = val * 1000
                    elif unit == "tạ":
                        result["yield_kg"] = val * 100
                    else:
                        result["yield_kg"] = val
                    break

    # ===== 7. CHẤT LƯỢNG (QUALITY) =====
    quality_keywords = [
        ("loại 1", "Loại 1 (Cao cấp)"),
        ("loại một", "Loại 1 (Cao cấp)"),
        ("loại 2", "Loại 2"),
        ("loại hai", "Loại 2"),
        ("xuất khẩu", "Đạt chuẩn Xuất khẩu"),
        ("vietgap", "Đạt chuẩn VietGAP"),
        ("đạt chuẩn", "Đạt chuẩn VietGAP"),
    ]
    for keyword, label in quality_keywords:
        if keyword in text_lower:
            result["quality"] = label
            break
    
    # Mặc định chất lượng nếu có "thu hoạch"
    if not result["quality"] and ("thu hoạch" in text_lower or result["harvest_date"]):
        result["quality"] = "Đạt chuẩn VietGAP"

    # ===== 8. ĐỘ NGỌT BRIX (BRIX VALUE) =====
    # Tìm brix hoặc độ ngọt theo sau hoặc đứng trước bởi số
    brix_match = re.search(
        r'(?:brix|độ ngọt|chỉ số brix)\s*[:\-]?\s*(\d+(?:[\.,]\d+)?)\b',
        text_lower
    )
    if brix_match:
        result["brix_value"] = float(brix_match.group(1).replace(',', '.'))
    else:
        # Thử tìm số và chữ brix đảo ngược: e.g. "12 brix", "12.5 brix"
        brix_match2 = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:brix|độ ngọt)\b', text_lower)
        if brix_match2:
            result["brix_value"] = float(brix_match2.group(1).replace(',', '.'))

    return result

