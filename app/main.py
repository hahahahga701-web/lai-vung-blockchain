import os
import sys
import io
import logging
import traceback

# Setup logging to help with debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Safe encoding for console output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Fallback for older Python versions
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import (
    init_db, create_lot, update_transporter, update_distributor, 
    get_lot, list_lots, tamper_database_sim
)
from app.blockchain import (
    Blockchain, compute_farmer_hash, compute_transporter_hash, 
    compute_distributor_hash
)
from app.ai_helper import parse_vietnamese_speech, LLM_PROMPT_TEMPLATE
from app.vietgap_standards import (
    get_fertilizer_autocomplete, get_pesticide_autocomplete,
    get_all_fertilizers_grouped, get_all_pesticides_grouped
)
from datetime import timedelta

# ============= DATA VALIDATION HELPERS =============
def validate_farmer_data(data):
    """Xác thực dữ liệu nông dân để tránh dữ liệu tạm thời không khớp."""
    errors = []
    
    # Kiểm tra mã lô
    if not data.lot_id or not data.lot_id.strip():
        errors.append("Mã lô không được để trống")
    elif len(data.lot_id) > 50:
        errors.append("Mã lô không được vượt quá 50 ký tự")
    
    # Kiểm tra mã vùng trồng
    if not data.planting_area_code or not data.planting_area_code.strip():
        errors.append("Mã vùng trồng không được để trống")
    
    # Kiểm tra ngày đặc biệt
    if not data.planting_date or not data.harvest_date:
        errors.append("Ngày trồng và ngày thu hoạch không được để trống")
    else:
        try:
            plant_date = datetime.strptime(str(data.planting_date), "%Y-%m-%d")
            harvest_date = datetime.strptime(str(data.harvest_date), "%Y-%m-%d")
            
            if harvest_date < plant_date:
                errors.append("Ngày thu hoạch không thể sớm hơn ngày trồng")
        except (ValueError, TypeError) as e:
            errors.append(f"Định dạng ngày không hợp lệ: {str(e)}")
    
    # Kiểm tra ngày phun thuốc cuối cùng
    if data.last_spray_date:
        try:
            spray_date = datetime.strptime(str(data.last_spray_date), "%Y-%m-%d")
            harvest_date = datetime.strptime(str(data.harvest_date), "%Y-%m-%d")
            if spray_date > harvest_date:
                errors.append("Ngày phun thuốc không thể muộn hơn ngày thu hoạch")
        except (ValueError, TypeError):
            errors.append("Định dạng ngày phun thuốc không hợp lệ")
    
    # Kiểm tra Độ Brix
    if data.brix_value:
        try:
            brix = float(data.brix_value)
            if brix < 0 or brix > 30:
                errors.append("Độ Brix phải nằm trong khoảng 0-30")
        except (ValueError, TypeError):
            errors.append("Độ Brix phải là số")
    
    # Kiểm tra năng suất
    try:
        yield_str = str(data.yield_kg).strip()
        if not yield_str or yield_str.lower() == 'nan':
            errors.append("Năng suất (kg) không được để trống")
        else:
            yield_value = float(yield_str)
            if yield_value < 0:
                errors.append("Năng suất không thể âm")
            elif yield_value > 1000000:  # Hợp lý cho lô hàng
                errors.append("Năng suất quá lớn (>1,000,000 kg)")
    except (ValueError, TypeError):
        errors.append("Năng suất phải là số")
    
    # Kiểm tra các trường chính
    if not data.variety or not data.variety.strip():
        errors.append("Loại quýt không được để trống")
    if not data.quality or not data.quality.strip():
        errors.append("Chất lượng không được để trống")
    if not data.fertilizer or not data.fertilizer.strip():
        errors.append("Nhật ký phân bón không được để trống")
    if not data.pesticide or not data.pesticide.strip():
        errors.append("Thuốc BVTV không được để trống")
    
    return errors

def validate_transporter_data(data):
    """Xác thực dữ liệu vận chuyển."""
    errors = []
    
    # Kiểm tra thông tin vận chuyển cơ bản
    if not data.transporter_name or not data.transporter_name.strip():
        errors.append("Tên đơn vị vận chuyển không được để trống")
    if not data.vehicle_plate or not data.vehicle_plate.strip():
        errors.append("Biển số xe không được để trống")
    if not data.driver_code or not data.driver_code.strip():
        errors.append("Mã tài xế không được để trống")
    
    try:
        pickup_date = datetime.fromisoformat(data.pickup_date.replace(" ", "T"))
        delivery_date = datetime.fromisoformat(data.delivery_date.replace(" ", "T"))
        
        if delivery_date < pickup_date:
            errors.append("Ngày giao không thể sớm hơn ngày nhận hàng")
        
        # Kiểm tra thời gian hợp lý (không quá 30 ngày)
        days_diff = (delivery_date - pickup_date).days
        if days_diff > 30:
            errors.append("Thời gian vận chuyển quá dài (>30 ngày)")
    except ValueError as e:
        errors.append(f"Định dạng thời gian không hợp lệ: {str(e)}")
    
    # Kiểm tra nhiệt độ
    try:
        if float(data.temperature) < -50 or float(data.temperature) > 50:
            errors.append("Nhiệt độ không hợp lệ (nên trong khoảng -50 đến 50°C)")
    except (ValueError, TypeError):
        errors.append("Nhiệt độ phải là số")
    
    # Kiểm tra độ ẩm nếu có
    if data.humidity:
        try:
            if float(data.humidity) < 0 or float(data.humidity) > 100:
                errors.append("Độ ẩm phải nằm trong khoảng 0-100%")
        except (ValueError, TypeError):
            errors.append("Độ ẩm phải là số")
    
    # Kiểm tra cân nặng
    if data.weight_at_pickup and data.weight_at_delivery:
        try:
            weight_pickup = float(data.weight_at_pickup)
            weight_delivery = float(data.weight_at_delivery)
            if weight_delivery > weight_pickup:
                errors.append("Cân nặng khi giao không thể lớn hơn lúc nhận")
        except (ValueError, TypeError):
            errors.append("Cân nặng phải là số")
    
    if not data.condition or not data.condition.strip():
        errors.append("Trạng thái hàng hóa không được để trống")
    if not data.transit_time or not data.transit_time.strip():
        errors.append("Thời gian vận chuyển không được để trống")
    
    return errors

def validate_distributor_data(data):
    """Xác thực dữ liệu phân phối."""
    errors = []
    
    if not data.storage_condition or not data.storage_condition.strip():
        errors.append("Điều kiện lưu kho không được để trống")
    
    try:
        warehouse_date = datetime.strptime(data.warehouse_date, "%Y-%m-%d")
        retail_date = datetime.strptime(data.retail_date, "%Y-%m-%d")
        
        if retail_date < warehouse_date:
            errors.append("Ngày bày bán không thể sớm hơn ngày nhập kho")
        
        if data.shelf_date:
            shelf_date = datetime.strptime(data.shelf_date, "%Y-%m-%d")
            if shelf_date < warehouse_date:
                errors.append("Ngày lên kệ không thể sớm hơn ngày nhập kho")
    except ValueError as e:
        errors.append(f"Định dạng ngày không hợp lệ: {str(e)}")
    
    return errors

app = FastAPI(
    title="Lai Vung Mandarin Traceability System",
    description="Hệ thống truy xuất nguồn gốc Quýt Hồng Lai Vung - Blockchain & AI Hybrid",
    version="1.0.0"
)

# Khởi tạo DB và Blockchain
init_db()
blockchain = Blockchain()

# Mount thư mục static phục vụ frontend
# Tạo thư mục static nếu chưa tồn tại
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

# Định nghĩa các mô hình dữ liệu (Pydantic Models)

class VoiceInput(BaseModel):
    text: str

class FarmerSubmitInput(BaseModel):
    lot_id: str
    variety: str
    planting_area_code: str
    planting_date: str
    last_spray_date: Optional[str] = None
    fertilizer: str
    pesticide: str
    harvest_date: str
    yield_kg: float
    quality: str
    brix_value: Optional[float] = None
    post_harvest_washing: bool = False
    post_harvest_sorting: bool = False
    post_harvest_packaging: bool = False

class TransporterUpdateInput(BaseModel):
    lot_id: str
    transporter_name: str
    vehicle_plate: str
    driver_code: str
    pickup_date: str
    pickup_time: Optional[str] = None
    eta: Optional[str] = None
    transit_time: str
    temperature: float
    humidity: Optional[float] = None
    condition: str
    delivery_date: str
    weight_at_pickup: Optional[float] = None
    weight_at_delivery: Optional[float] = None

class DistributorUpdateInput(BaseModel):
    lot_id: str
    warehouse_date: str
    shelf_date: Optional[str] = None
    storage_condition: str
    display_condition: Optional[str] = None
    shelf_life_expiry: Optional[str] = None
    retail_date: str

class TamperInput(BaseModel):
    lot_id: str
    field: str
    value: str

# ----------------- APIS -----------------

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    """Trả về trang giao diện chính."""
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h2>Frontend index.html chưa được khởi tạo.</h2>")

@app.post("/api/ai/parse-voice")
async def parse_voice(data: VoiceInput):
    """
    API tích hợp Cerebras Llama 3.1-70b:
    Nhận chuỗi văn bản tiếng Việt thô và phân tích cấu trúc JSON với đầy đủ chẩn đoán.
    """
    try:
        parsed_data = await parse_vietnamese_speech(data.text)
        return {
            "success": True,
            "raw_text": data.text,
            "parsed_data": parsed_data,
            "is_complete": parsed_data.get("is_complete", False),
            "missing_fields": parsed_data.get("missing_fields", []),
            "feedback_message": parsed_data.get("feedback_message", "Phân tích thành công."),
            "prompt_used": LLM_PROMPT_TEMPLATE  # Don't format with user input to avoid issues
        }
    except Exception as e:
        import traceback
        print(f"[ERROR] Parse voice endpoint failed: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/farmer/submit")
def submit_farmer_data(data: FarmerSubmitInput):
    """
    Giai đoạn 1: Nông dân gửi thông tin trồng trọt.
    Ghi dữ liệu vào SQLite và đẩy mã băm (hash) lên Blockchain.
    """
    try:
        # ✓ XÁC THỰC DỮ LIỆU ĐẦU VÀO
        validation_errors = validate_farmer_data(data)
        if validation_errors:
            print(f"[ERROR] Farmer validation failed: {validation_errors}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Dữ liệu không hợp lệ",
                    "errors": validation_errors
                }
            )
        
        # Kiểm tra lô hàng đã tồn tại trên hệ thống chưa để tránh ghi đè dữ liệu cũ
        existing_lot = get_lot(data.lot_id)
        if existing_lot:
            raise HTTPException(
                status_code=400, 
                detail=f"Lô hàng {data.lot_id} đã tồn tại trên hệ thống và không thể sửa đổi hoặc khởi tạo lại."
            )
            
        # Tính toán mã băm dữ liệu nông dân
        farmer_hash = compute_farmer_hash(
            lot_id=data.lot_id,
            variety=data.variety,
            planting_date=data.planting_date,
            fertilizer=data.fertilizer,
            pesticide=data.pesticide,
            harvest_date=data.harvest_date,
            yield_kg=data.yield_kg,
            quality=data.quality
        )
        
        # Lưu SQLite
        create_lot(data.dict(), farmer_hash)
        
        # Đẩy lên Blockchain
        tx = blockchain.add_transaction(
            lot_id=data.lot_id,
            stage="FARMER_STAGE",
            data_hash=farmer_hash
        )
        
        return {
            "success": True,
            "message": f"Khởi tạo thành công lô {data.lot_id}",
            "farmer_hash": farmer_hash,
            "blockchain_transaction": tx
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_farmer_data for lot {data.lot_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "Loi trong xu ly giao dich", "error": str(e)}
        )

@app.post("/api/transporter/update")
def update_transport_data(data: TransporterUpdateInput):
    """
    Giai đoạn 2: Đơn vị vận chuyển cập nhật trạng thái di chuyển.
    Ghi dữ liệu vào SQLite và đẩy mã băm lên Blockchain.
    """
    try:
        # ✓ XÁC THỰC DỮ LIỆU ĐẦU VÀO
        validation_errors = validate_transporter_data(data)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Dữ liệu không hợp lệ",
                    "errors": validation_errors
                }
            )
        
        lot = get_lot(data.lot_id)
        if not lot:
            raise HTTPException(status_code=404, detail="Không tìm thấy lô hàng này")
            
        # Kiểm tra trạng thái hiện tại để đảm bảo không ghi đè khi đã vận chuyển xong
        if lot.get("current_stage") != "FARMER":
            raise HTTPException(
                status_code=400, 
                detail="Lô hàng này đã được vận chuyển hoặc hoàn thành phân phối, không thể chỉnh sửa lại."
            )
            
        transporter_hash = compute_transporter_hash(
            lot_id=data.lot_id,
            pickup_date=data.pickup_date,
            transit_time=data.transit_time,
            temperature=data.temperature,
            condition=data.condition,
            delivery_date=data.delivery_date
        )
        
        # Cập nhật SQLite
        update_transporter(data.lot_id, data.dict(), transporter_hash)
        
        # Ghi nhận blockchain
        tx = blockchain.add_transaction(
            lot_id=data.lot_id,
            stage="TRANSPORT_STAGE",
            data_hash=transporter_hash
        )
        
        return {
            "success": True,
            "message": f"Cập nhật thông tin vận chuyển cho lô {data.lot_id}",
            "transporter_hash": transporter_hash,
            "blockchain_transaction": tx
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_transport_data for lot {data.lot_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "Loi trong xu ly giao dich", "error": str(e)}
        )

@app.post("/api/distributor/update")
def update_distributor_data(data: DistributorUpdateInput):
    """
    Giai đoạn 3: Nhà phân phối cập nhật trạng thái lưu kho, bày bán.
    Ghi dữ liệu vào SQLite và đẩy mã băm lên Blockchain.
    """
    try:
        # ✓ XÁC THỰC DỮ LIỆU ĐẦU VÀO
        validation_errors = validate_distributor_data(data)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": "Dữ liệu không hợp lệ",
                    "errors": validation_errors
                }
            )
        
        lot = get_lot(data.lot_id)
        if not lot:
            raise HTTPException(status_code=404, detail="Không tìm thấy lô hàng này")
            
        # Kiểm tra trạng thái hiện tại để đảm bảo tính đúng đắn của quy trình chuỗi cung ứng
        if lot.get("current_stage") == "FARMER":
            raise HTTPException(
                status_code=400, 
                detail="Lô hàng này chưa được vận chuyển, không thể cập nhật phân phối."
            )
        elif lot.get("current_stage") == "DISTRIBUTOR":
            raise HTTPException(
                status_code=400, 
                detail="Lô hàng này đã được xác nhận phân phối xong và không thể chỉnh sửa lại."
            )
            
        distributor_hash = compute_distributor_hash(
            lot_id=data.lot_id,
            warehouse_date=data.warehouse_date,
            storage_condition=data.storage_condition,
            retail_date=data.retail_date
        )
        
        # Cập nhật SQLite
        update_distributor(data.lot_id, data.dict(), distributor_hash)
        
        # Ghi nhận blockchain
        tx = blockchain.add_transaction(
            lot_id=data.lot_id,
            stage="DISTRIBUTOR_STAGE",
            data_hash=distributor_hash
        )
        
        return {
            "success": True,
            "message": f"Cập nhật thông tin phân phối cho lô {data.lot_id}",
            "distributor_hash": distributor_hash,
            "blockchain_transaction": tx
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_distributor_data for lot {data.lot_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "Loi trong xu ly giao dich", "error": str(e)}
        )

@app.api_route("/api/trace/{lot_id}", methods=["GET", "HEAD"])
def trace_lot(lot_id: str):
    """
    API dành cho Người Tiêu Dùng:
    Truy xuất toàn bộ vòng đời lô hàng và đối chiếu trực tiếp mã băm 
    từ SQLite với Blockchain để xác thực tính toàn vẹn của dữ liệu.
    """
    lot = get_lot(lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin cho mã lô này")

    # 1. Xác thực giai đoạn Nông dân
    calculated_farmer_hash = compute_farmer_hash(
        lot_id=lot["lot_id"],
        variety=lot["variety"],
        planting_date=lot["planting_date"],
        fertilizer=lot["fertilizer"],
        pesticide=lot["pesticide"],
        harvest_date=lot["harvest_date"],
        yield_kg=lot["yield_kg"],
        quality=lot["quality"]
    )
    blockchain_farmer_hash = blockchain.get_registered_hash(lot_id, "FARMER_STAGE")
    farmer_verified = (calculated_farmer_hash == blockchain_farmer_hash) if blockchain_farmer_hash else False

    # 2. Xác thực giai đoạn Vận chuyển
    transport_verified = False
    calculated_transporter_hash = None
    blockchain_transporter_hash = None
    if lot["pickup_date"]:
        calculated_transporter_hash = compute_transporter_hash(
            lot_id=lot["lot_id"],
            pickup_date=lot["pickup_date"],
            transit_time=lot["transit_time"],
            temperature=lot["temperature"],
            condition=lot["condition"],
            delivery_date=lot["delivery_date"]
        )
        blockchain_transporter_hash = blockchain.get_registered_hash(lot_id, "TRANSPORT_STAGE")
        transport_verified = (calculated_transporter_hash == blockchain_transporter_hash) if blockchain_transporter_hash else False

    # 3. Xác thực giai đoạn Phân phối
    distributor_verified = False
    calculated_distributor_hash = None
    blockchain_distributor_hash = None
    if lot["warehouse_date"]:
        calculated_distributor_hash = compute_distributor_hash(
            lot_id=lot["lot_id"],
            warehouse_date=lot["warehouse_date"],
            storage_condition=lot["storage_condition"],
            retail_date=lot["retail_date"]
        )
        blockchain_distributor_hash = blockchain.get_registered_hash(lot_id, "DISTRIBUTOR_STAGE")
        distributor_verified = (calculated_distributor_hash == blockchain_distributor_hash) if blockchain_distributor_hash else False

    # Hệ thống được xác thực là toàn vẹn nếu tất cả các giai đoạn đã kích hoạt đều khớp hash
    all_stages = True
    if not farmer_verified:
        all_stages = False
    if lot["pickup_date"] and not transport_verified:
        all_stages = False
    if lot["warehouse_date"] and not distributor_verified:
        all_stages = False

    return {
        "lot_id": lot_id,
        "current_stage": lot["current_stage"],
        "last_updated": lot["last_updated"],
        "data": {
            "farmer": {
                "variety": lot["variety"],
                "planting_date": lot["planting_date"],
                "fertilizer": lot["fertilizer"],
                "pesticide": lot["pesticide"],
                "harvest_date": lot["harvest_date"],
                "yield_kg": lot["yield_kg"],
                "quality": lot["quality"]
            },
            "transporter": {
                "pickup_date": lot["pickup_date"],
                "transit_time": lot["transit_time"],
                "temperature": lot["temperature"],
                "condition": lot["condition"],
                "delivery_date": lot["delivery_date"]
            } if lot["pickup_date"] else None,
            "distributor": {
                "warehouse_date": lot["warehouse_date"],
                "storage_condition": lot["storage_condition"],
                "retail_date": lot["retail_date"]
            } if lot["warehouse_date"] else None
        },
        "blockchain_verification": {
            "is_tampered": not all_stages,
            "farmer": {
                "computed_hash": calculated_farmer_hash,
                "blockchain_hash": blockchain_farmer_hash,
                "verified": farmer_verified
            },
            "transporter": {
                "computed_hash": calculated_transporter_hash,
                "blockchain_hash": blockchain_transporter_hash,
                "verified": transport_verified
            } if lot["pickup_date"] else None,
            "distributor": {
                "computed_hash": calculated_distributor_hash,
                "blockchain_hash": blockchain_distributor_hash,
                "verified": distributor_verified
            } if lot["warehouse_date"] else None
        }
    }

# ============= AUTOCOMPLETE & STANDARDS APIS =============

@app.api_route("/api/vietgap/fertilizers", methods=["GET", "HEAD"])
def get_fertilizers_list():
    """Lấy danh sách phân bón được phép sử dụng theo VietGAP."""
    return get_all_fertilizers_grouped()

@app.api_route("/api/vietgap/pesticides", methods=["GET", "HEAD"])
def get_pesticides_list():
    """Lấy danh sách thuốc BVTV được phép sử dụng theo VietGAP."""
    return get_all_pesticides_grouped()

@app.api_route("/api/vietgap/fertilizers/search", methods=["GET", "HEAD"])
def search_fertilizers(q: str = ""):
    """Tìm kiếm phân bón theo từ khóa (autocomplete)."""
    results = get_fertilizer_autocomplete(q)
    return {"results": results, "count": len(results)}

@app.api_route("/api/vietgap/pesticides/search", methods=["GET", "HEAD"])
def search_pesticides(q: str = ""):
    """Tìm kiếm thuốc BVTV theo từ khóa (autocomplete)."""
    results = get_pesticide_autocomplete(q)
    return {"results": results, "count": len(results)}

class PHICalculationInput(BaseModel):
    last_spray_date: str  # Format: YYYY-MM-DD
    harvest_date: str     # Format: YYYY-MM-DD
    phi_days: int = 14    # Số ngày PHI chuẩn (thường là 14 ngày)

@app.post("/api/farmer/calculate-phi")
def calculate_phi(data: PHICalculationInput):
    """
    Tính toán thời gian cách ly thuốc BVTV (PHI - Pre-Harvest Interval).
    Cảnh báo nông dân xem đã đủ an toàn để hái chưa.
    """
    try:
        spray_date = datetime.strptime(data.last_spray_date, "%Y-%m-%d")
        harvest_date = datetime.strptime(data.harvest_date, "%Y-%m-%d")
        
        days_elapsed = (harvest_date - spray_date).days
        days_remaining = data.phi_days - days_elapsed
        is_safe = days_elapsed >= data.phi_days
        
        return {
            "success": True,
            "last_spray_date": data.last_spray_date,
            "harvest_date": data.harvest_date,
            "required_phi_days": data.phi_days,
            "days_elapsed": days_elapsed,
            "days_remaining": max(0, days_remaining),
            "is_safe_to_harvest": is_safe,
            "status": "✅ AN TOÀN - Có thể hái" if is_safe else f"⚠️ CHƯA AN TOÀN - Vui lòng chờ {days_remaining} ngày nữa",
            "message": f"Nếu phun thuốc ngày {data.last_spray_date}, phải đợi ít nhất {data.phi_days} ngày mới được hái vào {harvest_date}. Hiện tại đã {days_elapsed} ngày."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Lỗi định dạng ngày: {str(e)}")

class ShelfLifeCalculationInput(BaseModel):
    harvest_date: str     # Format: YYYY-MM-DD
    warehouse_date: str   # Format: YYYY-MM-DD
    storage_condition: str  # e.g., "4-8°C lạnh", "15-20°C thường"
    shelf_life_days: int = 30  # Số ngày bảo quản tối đa

@app.post("/api/distributor/calculate-shelf-life")
def calculate_shelf_life(data: ShelfLifeCalculationInput):
    """
    Tính toán ngày hạn sử dụng được khuyến nghị (Shelf Life).
    Dựa trên ngày thu hoạch, điều kiện lưu kho để đề xuất ngày sử dụng tốt nhất.
    """
    try:
        harvest_date = datetime.strptime(data.harvest_date, "%Y-%m-%d")
        warehouse_date = datetime.strptime(data.warehouse_date, "%Y-%m-%d")
        
        days_since_harvest = (warehouse_date - harvest_date).days
        expiry_date = warehouse_date + timedelta(days=data.shelf_life_days - days_since_harvest)
        days_until_expiry = (expiry_date - warehouse_date).days
        
        return {
            "success": True,
            "harvest_date": data.harvest_date,
            "warehouse_date": data.warehouse_date,
            "storage_condition": data.storage_condition,
            "days_since_harvest": days_since_harvest,
            "shelf_life_days": data.shelf_life_days,
            "remaining_shelf_life": days_until_expiry,
            "recommended_use_by_date": expiry_date.strftime("%Y-%m-%d"),
            "message": f"Sản phẩm vào kho ngày {data.warehouse_date}. Khuyến khích sử dụng trước ngày {expiry_date.strftime('%Y-%m-%d')} (còn {days_until_expiry} ngày).",
            "storage_note": f"Bảo quản ở {data.storage_condition} để giữ độ tươi tối ưu."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Lỗi định dạng ngày: {str(e)}")

@app.api_route("/api/lots", methods=["GET", "HEAD"])
def get_lots_list():
    """Lấy danh sách tóm tắt các lô để điền nhanh trên giao diện."""
    return list_lots()

@app.api_route("/api/blockchain/blocks", methods=["GET", "HEAD"])
def get_blockchain_blocks():
    """API cho Explorer xem danh sách các block trong chuỗi khối."""
    return [block.to_dict() for block in blockchain.chain]

@app.post("/api/tamper")
def tamper_database(data: TamperInput):
    """API đặc biệt để người dùng bấm nút giả lập hacker sửa dữ liệu SQL."""
    try:
        success = tamper_database_sim(data.lot_id, data.field, data.value)
        return {
            "success": success,
            "message": f"Đã hack đổi cột '{data.field}' của lô {data.lot_id} thành '{data.value}' trong SQLite thành công!"
        }
    except Exception as e:
        logger.error(f"Error in tamper_database for lot {data.lot_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "Loi trong xu ly du lieu", "error": str(e)}
        )

@app.api_route("/product/{lot_id}", methods=["GET", "HEAD"])
def product_lot_html(lot_id: str):
    """
    Trang HTML hiển thị thông tin chi tiết lô hàng - Dành cho quét QR Code (URL từ Zalo/Camera).
    Người tiêu dùng quét QR bằng Zalo/Camera sẽ được dẫn đến trang này.
    """
    lot = get_lot(lot_id)
    if not lot:
        return HTMLResponse("""
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Không tìm thấy lô hàng - Lai Vung Trace</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
            <style>
                :root {
                    --bg-dark: #05070F;
                    --bg-card: rgba(22, 24, 33, 0.75);
                    --accent-orange: #ff7a00;
                    --accent-orange-glow: rgba(255, 122, 0, 0.35);
                    --border-color: rgba(255, 255, 255, 0.08);
                    --text-primary: #f5f6f8;
                    --text-secondary: #9aa0a6;
                }
                body {
                    font-family: 'Outfit', sans-serif;
                    background: var(--bg-dark);
                    color: var(--text-primary);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                    background-image: 
                        radial-gradient(circle at 10% 20%, rgba(255, 122, 0, 0.08) 0%, transparent 40%),
                        radial-gradient(circle at 90% 80%, rgba(255, 184, 0, 0.05) 0%, transparent 40%);
                }
                .container {
                    background: var(--bg-card);
                    border: 1px solid var(--border-color);
                    border-radius: 20px;
                    padding: 40px;
                    text-align: center;
                    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
                    max-width: 480px;
                    backdrop-filter: blur(12px);
                    margin: 20px;
                    box-shadow: 0 0 30px var(--accent-orange-glow);
                }
                .warn-icon {
                    font-size: 64px;
                    color: #ff3838;
                    margin-bottom: 20px;
                    filter: drop-shadow(0 0 10px rgba(255, 56, 56, 0.5));
                    animation: pulse 2s infinite;
                }
                h1 {
                    color: var(--text-primary);
                    font-size: 24px;
                    font-weight: 800;
                    margin-bottom: 12px;
                    letter-spacing: 0.5px;
                }
                p {
                    color: var(--text-secondary);
                    font-size: 15px;
                    line-height: 1.6;
                    margin-bottom: 16px;
                }
                .lot-label {
                    background: rgba(255,255,255,0.05);
                    padding: 4px 10px;
                    border-radius: 6px;
                    color: var(--accent-orange);
                    font-family: monospace;
                    font-weight: bold;
                    letter-spacing: 1px;
                }
                .btn-home {
                    display: inline-block;
                    margin-top: 25px;
                    padding: 12px 28px;
                    background: linear-gradient(135deg, var(--accent-orange) 0%, #ff5c00 100%);
                    color: white;
                    text-decoration: none;
                    font-weight: 600;
                    border-radius: 10px;
                    transition: all 0.3s;
                    box-shadow: 0 4px 15px var(--accent-orange-glow);
                }
                .btn-home:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(255,122,0,0.5);
                }
                @keyframes pulse {
                    0%, 100% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.05); opacity: 0.8; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="warn-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                <h1>Không tìm thấy lô hàng</h1>
                <p>Mã lô <span class="lot-label">""" + lot_id + """</span> không tồn tại trong hệ thống.</p>
                <p>Vui lòng quét đúng mã QR code chính thức trên bao bì của sản phẩm Quýt Hồng Lai Vung.</p>
                <a href="/" class="btn-home"><i class="fa-solid fa-house"></i> VỀ TRANG CHỦ</a>
            </div>
        </body>
        </html>
        """, status_code=404)

    # Lấy dữ liệu xác thực
    calculated_farmer_hash = compute_farmer_hash(
        lot_id=lot["lot_id"],
        variety=lot["variety"],
        planting_date=lot["planting_date"],
        fertilizer=lot["fertilizer"],
        pesticide=lot["pesticide"],
        harvest_date=lot["harvest_date"],
        yield_kg=lot["yield_kg"],
        quality=lot["quality"]
    )
    blockchain_farmer_hash = blockchain.get_registered_hash(lot_id, "FARMER_STAGE")
    farmer_verified = (calculated_farmer_hash == blockchain_farmer_hash) if blockchain_farmer_hash else False

    transport_verified = False
    blockchain_transporter_hash = None
    if lot["pickup_date"]:
        calculated_transporter_hash = compute_transporter_hash(
            lot_id=lot["lot_id"],
            pickup_date=lot["pickup_date"],
            transit_time=lot["transit_time"],
            temperature=lot["temperature"],
            condition=lot["condition"],
            delivery_date=lot["delivery_date"]
        )
        blockchain_transporter_hash = blockchain.get_registered_hash(lot_id, "TRANSPORT_STAGE")
        transport_verified = (calculated_transporter_hash == blockchain_transporter_hash) if blockchain_transporter_hash else False

    distributor_verified = False
    blockchain_distributor_hash = None
    if lot["warehouse_date"]:
        calculated_distributor_hash = compute_distributor_hash(
            lot_id=lot["lot_id"],
            warehouse_date=lot["warehouse_date"],
            storage_condition=lot["storage_condition"],
            retail_date=lot["retail_date"]
        )
        blockchain_distributor_hash = blockchain.get_registered_hash(lot_id, "DISTRIBUTOR_STAGE")
        distributor_verified = (calculated_distributor_hash == blockchain_distributor_hash) if blockchain_distributor_hash else False

    all_stages = farmer_verified and (not lot["pickup_date"] or transport_verified) and (not lot["warehouse_date"] or distributor_verified)
    is_tampered = not all_stages
    
    status_class = "verified" if not is_tampered else "tampered"
    status_text = "DỮ LIỆU BLOCKCHAIN TOÀN VẸN" if not is_tampered else "CẢNH BÁO: DỮ LIỆU BỊ THAY ĐỔI"
    status_icon = "fa-shield-halved" if not is_tampered else "fa-triangle-exclamation"

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Truy xuất nguồn gốc Quýt Hồng - {lot_id}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Share+Tech+Mono&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-dark: #05070f;
                --bg-card: rgba(22, 24, 33, 0.85);
                --accent-orange: #ff7a00;
                --accent-orange-glow: rgba(255, 122, 0, 0.35);
                --success-green: #1ccfb0;
                --success-glow: rgba(28, 207, 176, 0.3);
                --error-red: #ff3838;
                --error-glow: rgba(255, 56, 56, 0.3);
                --border-color: rgba(255, 255, 255, 0.08);
                --text-primary: #f5f6f8;
                --text-secondary: #9aa0a6;
                --font-mono: 'Share Tech Mono', monospace;
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Outfit', sans-serif;
                background-color: var(--bg-dark);
                color: var(--text-primary);
                min-height: 100vh;
                padding: 24px 16px;
                background-image: 
                    radial-gradient(circle at 10% 20%, rgba(255, 122, 0, 0.08) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(28, 207, 176, 0.04) 0%, transparent 40%);
                background-attachment: fixed;
            }}
            .container {{ max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }}
            
            /* Glassmorphic Header Card */
            .header-card {{
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                backdrop-filter: blur(12px);
                position: relative;
                overflow: hidden;
            }}
            .header-card::before {{
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; height: 3px;
                background: linear-gradient(90deg, var(--accent-orange), var(--success-green));
            }}
            .logo-icon {{
                width: 64px;
                height: 64px;
                margin: 0 auto 12px;
                border-radius: 50%;
                overflow: hidden;
                background: rgba(255,122,0,0.08);
                border: 2px solid rgba(255,122,0,0.25);
                box-shadow: 0 0 18px rgba(255,122,0,0.25);
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .logo-icon img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                border-radius: 50%;
            }}
            .header-card h1 {{
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 0.5px;
                background: linear-gradient(120deg, #fff 30%, var(--accent-orange) 80%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 4px;
            }}
            .lot-badge {{
                display: inline-block;
                background: rgba(255, 122, 0, 0.1);
                border: 1px solid rgba(255, 122, 0, 0.2);
                padding: 4px 12px;
                border-radius: 20px;
                font-family: var(--font-mono);
                font-size: 13px;
                color: var(--accent-orange);
                font-weight: bold;
                letter-spacing: 1px;
                margin-top: 6px;
            }}

            /* Security / Verification Badge */
            .status-badge {{
                border-radius: 12px;
                padding: 16px;
                text-align: center;
                font-weight: 700;
                font-size: 14px;
                letter-spacing: 0.5px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                backdrop-filter: blur(12px);
                border: 1px solid;
            }}
            .status-badge.verified {{
                background: rgba(28, 207, 176, 0.08);
                color: var(--success-green);
                border-color: rgba(28, 207, 176, 0.2);
                box-shadow: 0 0 20px var(--success-glow);
            }}
            .status-badge.tampered {{
                background: rgba(255, 56, 56, 0.08);
                color: var(--error-red);
                border-color: rgba(255, 56, 56, 0.2);
                box-shadow: 0 0 20px var(--error-glow);
            }}
            
            /* Timeline Section Card */
            .section-card {{
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 24px;
                backdrop-filter: blur(12px);
                position: relative;
            }}
            .section-title-row {{
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 16px;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 12px;
            }}
            .section-icon {{
                font-size: 20px;
                color: var(--accent-orange);
            }}
            .section-card.verified-stage .section-icon {{
                color: var(--success-green);
            }}
            .section-card h2 {{
                font-size: 16px;
                font-weight: 700;
                color: var(--text-primary);
            }}
            .stage-status {{
                margin-left: auto;
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 10px;
                font-weight: 600;
            }}
            .stage-status.ok {{
                background: rgba(28, 207, 176, 0.1);
                color: var(--success-green);
                border: 1px solid rgba(28, 207, 176, 0.2);
            }}
            .stage-status.warn {{
                background: rgba(255, 56, 56, 0.1);
                color: var(--error-red);
                border: 1px solid rgba(255, 56, 56, 0.2);
            }}

            .info-grid {{
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            .info-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 4px 0;
            }}
            .label {{
                font-size: 11px;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .value {{
                font-size: 14px;
                color: var(--text-primary);
                font-weight: 600;
                text-align: right;
            }}
            .value.hash {{
                font-family: var(--font-mono);
                font-size: 12px;
                color: rgba(28, 207, 176, 0.7);
                word-break: break-all;
                max-width: 200px;
            }}
            
            /* Footer */
            .footer {{
                text-align: center;
                padding: 16px 0;
                color: var(--text-secondary);
                font-size: 12px;
                line-height: 1.5;
                margin-top: 10px;
            }}
            .footer p i {{
                color: var(--success-green);
                margin-right: 4px;
            }}
            .blockchain-badge {{
                display: inline-block;
                background: rgba(28, 207, 176, 0.1);
                border: 1px solid rgba(28, 207, 176, 0.2);
                color: var(--success-green);
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
                margin-top: 8px;
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-card">
                <div class="logo-icon"><img src="/static/logo.webp" alt="Lai Vung Trace Logo"></div>
                <h1>LAI VUNG TRACE</h1>
                <p style="font-size:12px; color:var(--text-secondary);">Mã số nhận diện lô hàng</p>
                <div class="lot-badge">{lot_id}</div>
            </div>
            
            <div class="status-badge {status_class}">
                <i class="fa-solid {status_icon}"></i> {status_text}
            </div>
            
            <div class="content-flow" style="display:flex; flex-direction:column; gap:16px;">
                <!-- GIAI ĐOẠN NÔNG DÂN -->
                <div class="section-card verified-stage">
                    <div class="section-title-row">
                        <div class="section-icon"><i class="fa-solid fa-tractor"></i></div>
                        <h2>👨‍🌾 Nhật Ký Canh Tác & Thu Hoạch</h2>
                        <span class="stage-status {'ok' if farmer_verified else 'warn'}">{"✓ ĐÃ XÁC THỰC" if farmer_verified else "✗ CHƯA XÁC THỰC"}</span>
                    </div>
                    <div class="info-grid">
                        <div class="info-row"><span class="label">Giống Quýt:</span><span class="value">{lot['variety']}</span></div>
                        <div class="info-row"><span class="label">Chất Lượng:</span><span class="value">{lot['quality']}</span></div>
                        <div class="info-row"><span class="label">Ngày Gieo Trồng:</span><span class="value">{lot['planting_date']}</span></div>
                        <div class="info-row"><span class="label">Ngày Thu Hoạch:</span><span class="value">{lot['harvest_date']}</span></div>
                        <div class="info-row"><span class="label">Sản Lượng:</span><span class="value">{lot['yield_kg']} kg</span></div>
                        <div class="info-row"><span class="label">Phân Bón Hữu Cơ:</span><span class="value">{lot['fertilizer']}</span></div>
                        <div class="info-row"><span class="label">Thuốc BVTV Sinh Học:</span><span class="value">{lot['pesticide']}</span></div>
                        <div class="info-row"><span class="label">Mã Hóa Blockchain:</span><span class="value hash">{blockchain_farmer_hash if blockchain_farmer_hash else 'N/A'}</span></div>
                    </div>
                </div>
    """

    # GIAI ĐOẠN VẬN CHUYỂN
    if lot["pickup_date"]:
        html_content += f"""
                <div class="section-card verified-stage">
                    <div class="section-title-row">
                        <div class="section-icon"><i class="fa-solid fa-truck-fast"></i></div>
                        <h2>🚚 Nhật Ký Vận Chuyển</h2>
                        <span class="stage-status {'ok' if transport_verified else 'warn'}">{"✓ ĐÃ XÁC THỰC" if transport_verified else "✗ CHƯA XÁC THỰC"}</span>
                    </div>
                    <div class="info-grid">
                        <div class="info-row"><span class="label">Ngày Nhận Hàng:</span><span class="value">{lot['pickup_date']}</span></div>
                        <div class="info-row"><span class="label">Ngày Giao Hàng:</span><span class="value">{lot['delivery_date']}</span></div>
                        <div class="info-row"><span class="label">Thời Gian Vận Chuyển:</span><span class="value">{lot['transit_time']}</span></div>
                        <div class="info-row"><span class="label">Nhiệt Độ Thùng Lạnh:</span><span class="value">{lot['temperature']}°C</span></div>
                        <div class="info-row"><span class="label">Tình Trạng Lô Hàng:</span><span class="value">{lot['condition']}</span></div>
                        <div class="info-row"><span class="label">Mã Hóa Blockchain:</span><span class="value hash">{blockchain_transporter_hash if blockchain_transporter_hash else 'N/A'}</span></div>
                    </div>
                </div>
        """

    # GIAI ĐOẠN PHÂN PHỐI
    if lot["warehouse_date"]:
        html_content += f"""
                <div class="section-card verified-stage">
                    <div class="section-title-row">
                        <div class="section-icon"><i class="fa-solid fa-store"></i></div>
                        <h2>🏪 Nhật Ký Phân Phối & Bày Bán</h2>
                        <span class="stage-status {'ok' if distributor_verified else 'warn'}">{"✓ ĐÃ XÁC THỰC" if distributor_verified else "✗ CHƯA XÁC THỰC"}</span>
                    </div>
                    <div class="info-grid">
                        <div class="info-row"><span class="label">Ngày Nhập Kho:</span><span class="value">{lot['warehouse_date']}</span></div>
                        <div class="info-row"><span class="label">Điều Kiện Lưu Kho:</span><span class="value">{lot['storage_condition']}</span></div>
                        <div class="info-row"><span class="label">Ngày Bày Bán:</span><span class="value">{lot['retail_date']}</span></div>
                        <div class="info-row"><span class="label">Mã Hóa Blockchain:</span><span class="value hash">{blockchain_distributor_hash if blockchain_distributor_hash else 'N/A'}</span></div>
                    </div>
                </div>
        """

    html_content += f"""
                <!-- THÔNG TIN HỆ THỐNG -->
                <div class="section-card">
                    <div class="section-title-row">
                        <div class="section-icon"><i class="fa-solid fa-circle-info"></i></div>
                        <h2>⚙️ Đồng Bộ Hệ Thống</h2>
                    </div>
                    <div class="info-grid">
                        <div class="info-row"><span class="label">Cập Nhật Cuối:</span><span class="value">{lot['last_updated']}</span></div>
                        <div class="info-row"><span class="label">Trạng Thái Giao Dịch:</span><span class="value">{lot['current_stage']}</span></div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p><i class="fa-solid fa-shield-halved"></i> Hệ thống Blockchain đảm bảo dữ liệu không thể chỉnh sửa</p>
                <div class="blockchain-badge">VERIFIED ON ETHEREUM LEDGER</div>
                <p style="margin-top: 10px; font-size: 11px; color: var(--text-secondary);">Lai Vung Mandarin Traceability Network v1.1</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

# ============= CHATBOT AI ENDPOINT =============

CHATBOT_SYSTEM_PROMPT = """Chức năng: Trợ lý AI tích hợp trong hệ thống Quản lý và Truy xuất nguồn gốc Quýt Hồng Lai Vung (Lai Vung Trace Network).

1. TÍNH CÁCH & NGÔN NGỮ:
- Đóng vai một chàng trai miền Tây (Đồng Tháp) trẻ trung, thân thiện, chân thành và rành công nghệ.
- Giọng điệu lịch sự, niềm nở, luôn dùng các từ ngữ gần gũi như "dạ", "anh/chị", "bà con", "mình".
- TUYỆT ĐỐI KHÔNG lạm dụng từ địa phương quá sâu (chất phác, mộc mạc vừa phải, không dùng từ khó hiểu để người tiêu dùng mọi miền và bà con đều dễ đọc).

2. TÁC VỤ 1: HỖ TRỢ NÔNG DÂN NHẬP LIỆU (Giao diện Nhật ký canh tác)
- Giải thích các mục nhập liệu theo chuẩn VietGAP (Ví dụ: Mã lô hàng là gì, vì sao phải điền ngày phun thuốc cuối cùng, chỉ số độ ngọt Brix là gì...).
- Hướng dẫn các quy định pháp luật của Chính phủ về truy xuất nguồn gốc nông sản một cách ngắn gọn, dễ hiểu nhất, không dùng từ ngữ pháp lý khô khan.
- Động viên, hỗ trợ bà con khi họ gặp khó khăn trong việc gõ phím hoặc điền form.

3. TÁC VỤ 2: HỖ TRỢ NGƯỜI TIÊU DÙNG (Giao diện Cổng tra cứu)
- Khi người dùng nhập Mã sản phẩm (hoặc hệ thống chuyển dữ liệu chuỗi khối sang), AI có nhiệm vụ đọc dữ liệu gốc và TÓM TẮT ngắn gọn, rõ ràng cho người mua.
- Nội dung tóm tắt phải làm nổi bật được tính an toàn: Ngày trồng, ngày thu hoạch, thời gian cách ly thuốc bảo vệ thực vật an toàn, độ ngọt Brix (nếu có) và xác thực Blockchain an toàn.

4. NGUYÊN TẮC PHẢN HỒI & CHỐNG BỊA ĐẶT THÔNG TIN (ANTI-HALLUCINATION):
- TUYỆT ĐỐI KHÔNG tự bịa đặt (hallucinate) bất kỳ thông tin nào về tên nông dân (như bà Nguyễn Thị Lan, ông Nguyễn Văn A,...), tên nông trại, ngày trồng, ngày thu hoạch, phương thức sản xuất hay chỉ số độ ngọt nếu thông tin đó không xuất hiện trong "DỮ LIỆU LÔ HÀNG HIỆN TẠI" (context) được cung cấp.
- Nếu phần "DỮ LIỆU LÔ HÀNG HIỆN TẠI" trống hoặc không có thông tin của lô hàng người dùng đang hỏi, bạn bắt buộc phải nói rõ rằng: "Dạ hiện tại em chưa thấy dữ liệu của lô hàng này trên hệ thống Blockchain của hợp tác xã mình. Anh/chị vui lòng nhập mã sản phẩm hoặc quét mã QR trước để em tra cứu thông tin chính xác nhất giúp mình nha!".
- Chỉ tóm tắt trung thực, chính xác các trường dữ liệu thực tế được truyền vào trong context. Không tự suy diễn hay phỏng đoán thông tin thiếu.
- Định dạng rõ ràng bằng các dấu gạch đầu dòng để bà con dễ đọc."""

CHATBOT_API_KEY = "csk-62dwtj8mphpwydyf9x6nwnv4ep2fdw8m296k29fnykhknt9n"

from openai import AsyncOpenAI as _AsyncOpenAI
_chatbot_client = _AsyncOpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=CHATBOT_API_KEY
)

class ChatbotMessage(BaseModel):
    role: str  # "user" hoặc "assistant"
    content: str

class ChatbotInput(BaseModel):
    message: str
    history: Optional[List[ChatbotMessage]] = []
    context: Optional[str] = None  # Dữ liệu lô hàng nếu người tiêu dùng đang tra cứu

@app.post("/api/chatbot")
async def chatbot_endpoint(data: ChatbotInput):
    """
    API Chatbot AI - Trợ lý chàng trai miền Tây phục vụ nông dân và người tiêu dùng.
    Sử dụng Cerebras Llama-3.3-70b với system prompt chuyên biệt.
    """
    try:
        messages = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT}]
        
        # Nếu có context dữ liệu lô hàng, thêm vào system message
        if data.context:
            messages[0]["content"] += f"\n\nDỮ LIỆU LÔ HÀNG HIỆN TẠI (người dùng đang tra cứu):\n{data.context}"
        
        # Thêm lịch sử hội thoại
        for msg in (data.history or [])[-10:]:  # Giữ tối đa 10 tin gần nhất
            messages.append({"role": msg.role, "content": msg.content})
        
        # Thêm tin nhắn mới
        messages.append({"role": "user", "content": data.message})
        
        response = await _chatbot_client.chat.completions.create(
            model="gpt-oss-120b",
            messages=messages,
            temperature=0.7,
            max_tokens=512
        )
        
        reply = response.choices[0].message.content
        return {"success": True, "reply": reply}
    
    except Exception as e:
        print(f"[ERROR] Chatbot API failed: {str(e)}")
        return {
            "success": False,
            "reply": "Dạ em xin lỗi anh/chị ơi! Hệ thống đang bận xíu, anh/chị thử lại sau một chút nhé 🙏"
        }

# Mount static files (HTML, CSS, JS) - Cần được mount cuối cùng sau các route chính
app.mount("/static", StaticFiles(directory="static"), name="static")
