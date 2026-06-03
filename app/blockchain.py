import hashlib
import time
import json
import os
from app.git_helper import auto_commit_blockchain

# Use absolute path for blockchain ledger file to ensure it works on both local and Render
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(APP_DIR), "data")
os.makedirs(DATA_DIR, exist_ok=True)
LEDGER_PATH = os.path.join(DATA_DIR, "blockchain_ledger.json")

class Block:
    def __init__(self, index: int, timestamp: float, transactions: list, previous_hash: str, nonce: int = 0, hash_val: str = ""):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = hash_val or self.calculate_hash()

    def calculate_hash(self) -> str:
        """Tính toán mã băm SHA-256 cho khối."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty: int):
        """Mô phỏng Proof of Work - Đào khối bằng cách tìm nonce phù hợp."""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self, difficulty: int = 2):
        self.difficulty = difficulty
        self.pending_transactions = []
        self.chain = []
        self.load_chain()

    def create_genesis_block(self):
        """Khởi tạo khối khai sinh (Genesis Block)."""
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[{"info": "Genesis Block - He thong truy xuat nguon goc Quyt Hong Lai Vung"}],
            previous_hash="0" * 64
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_chain()

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, lot_id: str, stage: str, data_hash: str):
        """Thêm giao dịch băm dữ liệu mới vào hàng đợi (pending transactions)."""
        transaction = {
            "lot_id": lot_id,
            "stage": stage,
            "data_hash": data_hash,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        self.pending_transactions.append(transaction)
        
        # Để đảm bảo tính tức thời trong Demo, mỗi khi có giao dịch mới chúng ta sẽ tự động đào khối (Block) mới chứa giao dịch đó.
        self.mine_pending_transactions()
        return transaction

    def mine_pending_transactions(self):
        """Gộp các giao dịch chờ xử lý và đào một khối mới."""
        if not self.pending_transactions:
            return False

        latest_block = self.get_latest_block()
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=time.time(),
            transactions=self.pending_transactions,
            previous_hash=latest_block.hash
        )
        
        # Mining block
        new_block.mine_block(self.difficulty)
        
        # Thêm vào chain và xóa hàng đợi giao dịch
        self.chain.append(new_block)
        self.pending_transactions = []
        
        # Lưu vào file JSON
        self.save_chain()
        return new_block

    def get_registered_hash(self, lot_id: str, stage: str) -> str:
        """Tìm mã băm dữ liệu đã được ghi trên Blockchain cho một lô và giai đoạn nhất định."""
        # Duyệt từ cuối chuỗi khối lên để lấy giao dịch mới nhất (tránh lấy thông tin cũ của lot_id nếu có ghi đè)
        for block in reversed(self.chain):
            for tx in block.transactions:
                if tx.get("lot_id") == lot_id and tx.get("stage") == stage:
                    return tx.get("data_hash")
        return None

    def verify_chain(self) -> bool:
        """Kiểm tra tính toàn vẹn của chuỗi khối (Blockchain Integrity)."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]

            # Kiểm tra mã hash của block hiện tại có đúng không
            if current.hash != current.calculate_hash():
                return False

            # Kiểm tra liên kết khối
            if current.previous_hash != previous.hash:
                return False
            
            # Kiểm tra điều kiện độ khó (Proof of Work)
            if current.hash[:self.difficulty] != "0" * self.difficulty:
                return False

        return True

    def save_chain(self):
        """Lưu toàn bộ blockchain vào file JSON."""
        try:
            with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
                chain_data = [block.to_dict() for block in self.chain]
                json.dump(chain_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Lỗi lưu blockchain file: {e}")
            raise
        
        # 🔗 Tự động commit vào git để lưu vĩnh viễn (optional - không block nếu fail)
        try:
            # Get relative path for git command
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            relative_path = os.path.relpath(LEDGER_PATH, project_root)
            success, message = auto_commit_blockchain(relative_path, cwd=project_root)
            if success:
                try:
                    print(f"[Git] {message}")
                except Exception:
                    pass
        except Exception as e:
            try:
                print(f"[Git Warning] Không thể commit: {e}")
            except Exception:
                pass

    def load_chain(self):
        """Đọc blockchain từ file JSON nếu có, nếu chưa có thì tạo Genesis block."""
        if os.path.exists(LEDGER_PATH):
            try:
                with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                    chain_data = json.load(f)
                    self.chain = []
                    for item in chain_data:
                        block = Block(
                            index=item["index"],
                            timestamp=item["timestamp"],
                            transactions=item["transactions"],
                            previous_hash=item["previous_hash"],
                            nonce=item["nonce"],
                            hash_val=item["hash"]
                        )
                        self.chain.append(block)
            except Exception as e:
                print(f"Lỗi đọc Blockchain Ledger: {e}. Đang tạo mới...")
                self.create_genesis_block()
        else:
            self.create_genesis_block()

# Định nghĩa các hàm helper để sinh mã hash của từng giai đoạn dữ liệu

def compute_farmer_hash(lot_id: str, variety: str, planting_date: str, fertilizer: str, pesticide: str, harvest_date: str, yield_kg: float, quality: str) -> str:
    """Tạo mã băm SHA-256 từ thông tin của nông dân."""
    payload = f"farmer:{lot_id}:{variety or ''}:{planting_date or ''}:{fertilizer or ''}:{pesticide or ''}:{harvest_date or ''}:{yield_kg or 0.0}:{quality or ''}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def compute_transporter_hash(lot_id: str, pickup_date: str, transit_time: str, temperature: float, condition: str, delivery_date: str) -> str:
    """Tạo mã băm SHA-256 từ thông tin vận chuyển."""
    payload = f"transporter:{lot_id}:{pickup_date or ''}:{transit_time or ''}:{temperature or 0.0}:{condition or ''}:{delivery_date or ''}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def compute_distributor_hash(lot_id: str, warehouse_date: str, storage_condition: str, retail_date: str) -> str:
    """Tạo mã băm SHA-256 từ thông tin phân phối."""
    payload = f"distributor:{lot_id}:{warehouse_date or ''}:{storage_condition or ''}:{retail_date or ''}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()
