import sqlite3
import os
import json

# Use absolute path for database file to ensure it works on both local and Render
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(APP_DIR), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "blockchain_trace.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo cơ sở dữ liệu SQLite và bảng dữ liệu truy xuất nguồn gốc."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tạo bảng lưu trữ thông tin chuỗi cung ứng
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mandarin_lots (
            lot_id TEXT PRIMARY KEY,
            
            -- Giai đoạn 1: Nông dân / Hợp tác xã
            variety TEXT,
            planting_area_code TEXT,
            planting_date TEXT,
            last_spray_date TEXT,
            fertilizer TEXT,
            pesticide TEXT,
            harvest_date TEXT,
            phi_status TEXT,
            phi_days_remaining INTEGER,
            yield_kg REAL,
            quality TEXT,
            brix_value REAL,
            post_harvest_washing BOOLEAN DEFAULT 0,
            post_harvest_sorting BOOLEAN DEFAULT 0,
            post_harvest_packaging BOOLEAN DEFAULT 0,
            farmer_hash TEXT,
            
            -- Giai đoạn 2: Đơn vị vận chuyển
            transporter_name TEXT,
            vehicle_plate TEXT,
            driver_code TEXT,
            pickup_date TEXT,
            pickup_time TEXT,
            eta TEXT,
            transit_time TEXT,
            temperature REAL,
            humidity REAL,
            condition TEXT,
            delivery_date TEXT,
            weight_at_pickup REAL,
            weight_at_delivery REAL,
            weight_loss_kg REAL,
            weight_loss_percentage REAL,
            transporter_hash TEXT,
            
            -- Giai đoạn 3: Nhà phân phối
            warehouse_date TEXT,
            shelf_date TEXT,
            storage_condition TEXT,
            display_condition TEXT,
            shelf_life_expiry TEXT,
            retail_date TEXT,
            distributor_hash TEXT,
            
            -- Trạng thái chung
            current_stage TEXT DEFAULT 'FARMER',
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # ── Migration: tự động thêm các cột mới nếu bảng cũ thiếu ──
    cursor.execute("PRAGMA table_info(mandarin_lots)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    new_columns = [
        ("planting_area_code",      "TEXT"),
        ("last_spray_date",         "TEXT"),
        ("phi_status",              "TEXT"),
        ("phi_days_remaining",      "INTEGER"),
        ("brix_value",              "REAL"),
        ("post_harvest_washing",    "BOOLEAN DEFAULT 0"),
        ("post_harvest_sorting",    "BOOLEAN DEFAULT 0"),
        ("post_harvest_packaging",  "BOOLEAN DEFAULT 0"),
        ("transporter_name",        "TEXT"),
        ("vehicle_plate",           "TEXT"),
        ("driver_code",             "TEXT"),
        ("pickup_time",             "TEXT"),
        ("eta",                     "TEXT"),
        ("humidity",                "REAL"),
        ("weight_at_pickup",        "REAL"),
        ("weight_at_delivery",      "REAL"),
        ("weight_loss_kg",          "REAL"),
        ("weight_loss_percentage",  "REAL"),
        ("shelf_date",              "TEXT"),
        ("display_condition",       "TEXT"),
        ("shelf_life_expiry",       "TEXT"),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE mandarin_lots ADD COLUMN {col_name} {col_type}")
            print(f"[DB Migration] Added column: {col_name}")

    conn.commit()
    conn.close()

def create_lot(lot_data: dict, farmer_hash: str):
    """Tạo mới lô quýt ở giai đoạn nông dân."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO mandarin_lots (
            lot_id, variety, planting_area_code, planting_date, last_spray_date, 
            fertilizer, pesticide, harvest_date, phi_status, phi_days_remaining,
            yield_kg, quality, brix_value, post_harvest_washing, post_harvest_sorting, 
            post_harvest_packaging, farmer_hash, current_stage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'FARMER')
    ''', (
        lot_data['lot_id'],
        lot_data.get('variety'),
        lot_data.get('planting_area_code'),
        lot_data.get('planting_date'),
        lot_data.get('last_spray_date'),
        lot_data.get('fertilizer'),
        lot_data.get('pesticide'),
        lot_data.get('harvest_date'),
        lot_data.get('phi_status'),
        lot_data.get('phi_days_remaining'),
        lot_data.get('yield_kg'),
        lot_data.get('quality'),
        lot_data.get('brix_value'),
        lot_data.get('post_harvest_washing', 0),
        lot_data.get('post_harvest_sorting', 0),
        lot_data.get('post_harvest_packaging', 0),
        farmer_hash
    ))
    conn.commit()
    conn.close()

def update_transporter(lot_id: str, transport_data: dict, transporter_hash: str):
    """Cập nhật thông tin vận chuyển ở giai đoạn 2."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE mandarin_lots 
        SET transporter_name = ?, vehicle_plate = ?, driver_code = ?, 
            pickup_date = ?, pickup_time = ?, eta = ?, transit_time = ?, 
            temperature = ?, humidity = ?, condition = ?, delivery_date = ?, 
            weight_at_pickup = ?, weight_at_delivery = ?, weight_loss_kg = ?, 
            weight_loss_percentage = ?, transporter_hash = ?, 
            current_stage = 'TRANSPORT', last_updated = CURRENT_TIMESTAMP
        WHERE lot_id = ?
    ''', (
        transport_data.get('transporter_name'),
        transport_data.get('vehicle_plate'),
        transport_data.get('driver_code'),
        transport_data.get('pickup_date'),
        transport_data.get('pickup_time'),
        transport_data.get('eta'),
        transport_data.get('transit_time'),
        transport_data.get('temperature'),
        transport_data.get('humidity'),
        transport_data.get('condition'),
        transport_data.get('delivery_date'),
        transport_data.get('weight_at_pickup'),
        transport_data.get('weight_at_delivery'),
        transport_data.get('weight_loss_kg'),
        transport_data.get('weight_loss_percentage'),
        transporter_hash,
        lot_id
    ))
    conn.commit()
    conn.close()

def update_distributor(lot_id: str, distributor_data: dict, distributor_hash: str):
    """Cập nhật thông tin phân phối ở giai đoạn 3."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE mandarin_lots 
        SET warehouse_date = ?, shelf_date = ?, storage_condition = ?, 
            display_condition = ?, shelf_life_expiry = ?, retail_date = ?, 
            distributor_hash = ?, current_stage = 'DISTRIBUTOR', last_updated = CURRENT_TIMESTAMP
        WHERE lot_id = ?
    ''', (
        distributor_data.get('warehouse_date'),
        distributor_data.get('shelf_date'),
        distributor_data.get('storage_condition'),
        distributor_data.get('display_condition'),
        distributor_data.get('shelf_life_expiry'),
        distributor_data.get('retail_date'),
        distributor_hash,
        lot_id
    ))
    conn.commit()
    conn.close()

def get_lot(lot_id: str):
    """Truy vấn thông tin chi tiết của một lô hàng."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM mandarin_lots WHERE lot_id = ?', (lot_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def list_lots():
    """Lấy danh sách tất cả các lô hàng."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT lot_id, variety, current_stage, last_updated FROM mandarin_lots ORDER BY last_updated DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def tamper_database_sim(lot_id: str, field: str, fake_value: str):
    """Giả lập việc hacker/kẻ gian đột nhập cơ sở dữ liệu SQL để thay đổi thông tin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Cho phép sửa đổi bất kỳ trường nào để demo phát hiện lỗi băm
    cursor.execute(f'''
        UPDATE mandarin_lots
        SET {field} = ?
        WHERE lot_id = ?
    ''', (fake_value, lot_id))
    conn.commit()
    conn.close()
    return True
