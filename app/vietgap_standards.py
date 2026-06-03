"""
VietGAP Standards Database - Approved Fertilizers and Pesticides
Danh sách các loại phân bón và thuốc BVTV được phép sử dụng theo chuẩn VietGAP
"""

# Danh sách phân bón hữu cơ và hóa học được phép sử dụng trong VietGAP
APPROVED_FERTILIZERS = [
    # Phân bón hữu cơ
    {"name": "Phân chuồng hoai mục", "type": "organic", "category": "Hữu cơ"},
    {"name": "Phân ủ thành phố", "type": "organic", "category": "Hữu cơ"},
    {"name": "Phân bò hoai mục", "type": "organic", "category": "Hữu cơ"},
    {"name": "Phân gà lên men", "type": "organic", "category": "Hữu cơ"},
    {"name": "Cơm thừa lên men", "type": "organic", "category": "Hữu cơ"},
    
    # Phân bón hóa học chứng chỉ
    {"name": "Phân NPK 10-10-10", "type": "chemical", "category": "Hóa học"},
    {"name": "Phân Urê (N46)", "type": "chemical", "category": "Hóa học"},
    {"name": "Phân DAP (18-46-0)", "type": "chemical", "category": "Hóa học"},
    {"name": "Phân Kali clorua (KCl 60%)", "type": "chemical", "category": "Hóa học"},
    {"name": "Phân Lân (Super Phosphate)", "type": "chemical", "category": "Hóa học"},
    {"name": "Phân NPK 12-12-17", "type": "chemical", "category": "Hóa học"},
    {"name": "Phân NPK 15-15-15", "type": "chemical", "category": "Hóa học"},
    
    # Phân bón sinh học
    {"name": "Phân cây lên men vi sinh", "type": "bio", "category": "Sinh học"},
    {"name": "Phân Azospirillum (vi khuẩn cố định N)", "type": "bio", "category": "Sinh học"},
    {"name": "Phân Phosphobacteria (vi khuẩn hòa tan P)", "type": "bio", "category": "Sinh học"},
    {"name": "Phân EM (Hiệu tích Microorganism)", "type": "bio", "category": "Sinh học"},
    {"name": "Phân humic acid + Amino acid", "type": "bio", "category": "Sinh học"},
    
    # Phân bón lá
    {"name": "Phân lá Boron (B)", "type": "foliar", "category": "Dinh dưỡng Lá"},
    {"name": "Phân lá Kẽm (Zn)", "type": "foliar", "category": "Dinh dưỡng Lá"},
    {"name": "Phân lá Magie (Mg)", "type": "foliar", "category": "Dinh dưỡng Lá"},
    {"name": "Phân lá Canxi (Ca)", "type": "foliar", "category": "Dinh dưỡng Lá"},
]

# Danh sách thuốc BVTV được phép sử dụng trong VietGAP
APPROVED_PESTICIDES = [
    # Thuốc sinh học - An toàn độc lập
    {"name": "Chế phẩm Bacillus (chống sâu bệnh)", "type": "bio", "category": "Sinh học"},
    {"name": "Chế phẩm Beauveria bassiana (nấm trừ sâu)", "type": "bio", "category": "Sinh học"},
    {"name": "Chế phẩm Metarhizium (nấm trừ côn trùng)", "type": "bio", "category": "Sinh học"},
    {"name": "Nano bạc trừ sâu bệnh", "type": "nano", "category": "Công nghệ Nano"},
    {"name": "Nano oxit kẽm (ZnO) trừ nấm bệnh", "type": "nano", "category": "Công nghệ Nano"},
    
    # Hóa chất hữu cơ được phép
    {"name": "Dầu neem (Neem oil) trừ sâu", "type": "organic", "category": "Hữu cơ tự nhiên"},
    {"name": "Xà phòng thực vật (Plant soap)", "type": "organic", "category": "Hữu cơ tự nhiên"},
    {"name": "Axit acetic (Acetic acid) trừ nấm", "type": "organic", "category": "Hữu cơ tự nhiên"},
    {"name": "Lưu huỳnh (Sulfur) trừ nấm", "type": "chemical", "category": "Hóa chất cho phép"},
    
    # Thuốc hóa học cho phép trong VietGAP
    {"name": "Imidacloprid (Confidor)", "type": "chemical", "category": "Hóa chất"},
    {"name": "Metalaxyl (Ridomil) trừ nấm lùn", "type": "chemical", "category": "Hóa chất"},
    {"name": "Mancozeb (Dithane) trừ bệnh lá", "type": "chemical", "category": "Hóa chất"},
    {"name": "Carbendazim (Bavistin) trừ nấm", "type": "chemical", "category": "Hóa chất"},
    {"name": "Pyrethroid (Deltamethrin) trừ sâu", "type": "chemical", "category": "Hóa chất"},
    {"name": "Lambda-Cyhalothrin trừ sâu", "type": "chemical", "category": "Hóa chất"},
    {"name": "Abamectin trừ sâu bệnh", "type": "chemical", "category": "Hóa chất"},
    {"name": "Flubendiamide (Takumi) trừ sâu", "type": "chemical", "category": "Hóa chất"},
    
    # Thuốc đặc hiệu
    {"name": "Chlorothalonil (Bravo) trừ bệnh nấm", "type": "chemical", "category": "Hóa chất"},
    {"name": "Copper (Xanh lam) trừ bệnh vi khuẩn", "type": "chemical", "category": "Hóa chất"},
    {"name": "Bordeaux mixture (hỗn hợp Bordeaux) trừ bệnh nấm", "type": "chemical", "category": "Hóa chất"},
]

def get_fertilizer_autocomplete(search_text: str):
    """
    Tìm kiếm phân bón theo từ khóa
    """
    search_text = search_text.lower().strip()
    if not search_text:
        return APPROVED_FERTILIZERS
    
    return [f for f in APPROVED_FERTILIZERS if search_text in f["name"].lower()]

def get_pesticide_autocomplete(search_text: str):
    """
    Tìm kiếm thuốc BVTV theo từ khóa
    """
    search_text = search_text.lower().strip()
    if not search_text:
        return APPROVED_PESTICIDES
    
    return [p for p in APPROVED_PESTICIDES if search_text in p["name"].lower()]

def get_all_fertilizers_grouped():
    """Trả về danh sách phân bón theo nhóm"""
    grouped = {}
    for fertilizer in APPROVED_FERTILIZERS:
        category = fertilizer["category"]
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(fertilizer["name"])
    return grouped

def get_all_pesticides_grouped():
    """Trả về danh sách thuốc BVTV theo nhóm"""
    grouped = {}
    for pesticide in APPROVED_PESTICIDES:
        category = pesticide["category"]
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(pesticide["name"])
    return grouped
