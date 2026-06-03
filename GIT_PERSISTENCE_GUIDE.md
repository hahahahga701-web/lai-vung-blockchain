# 🔗 Git Auto-Commit Blockchain Persistence Guide

## 📋 Vấn Đề & Giải Pháp

### Vấn Đề Ban Đầu
Khi deploy trên **Render (free tier)**, ứng dụng tự động dừng lại sau 15 phút không hoạt động. Lúc này, tất cả dữ liệu blockchain (lưu trên hệ thống file) sẽ **bị xóa vĩnh viễn** vì Render sử dụng **ephemeral filesystem**.

### Giải Pháp: Git Auto-Commit
Chúng ta sẽ **tự động commit blockchain_ledger.json vào git** mỗi khi có thay đổi. Cách này:
- ✅ **Miễn phí** - không cần database bên ngoài
- ✅ **Đơn giản** - chỉ cần git
- ✅ **Vĩnh viễn** - dữ liệu lưu trên GitHub
- ✅ **Tự động** - không cần thao tác bручный

---

## 🛠️ Cách Hoạt Động

### 1. **Khi Có Giao Dịch Blockchain Mới**
```
User adds transaction → mine_pending_transactions() → save_chain() 
  → auto_commit_blockchain() → git commit + git push
```

### 2. **Các File Liên Quan**

| File | Chức Năng |
|------|----------|
| `app/git_helper.py` | Module xử lý git commit tự động |
| `app/blockchain.py` | Tích hợp auto-commit trong `save_chain()` |
| `run.py` | Khởi tạo git config khi startup |
| `.gitignore` | Đảm bảo track `blockchain_ledger.json` |

---

## 📦 Hướng Dẫn Deploy Trên Render

### **Yêu Cầu**
- Repository GitHub với project này
- Render account (miễn phí)
- Git credentials (Personal Access Token)

### **Bước 1: Tạo GitHub Personal Access Token**

1. Vào https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Đặt tên: `Render Blockchain`
4. Chọn scopes: ☑️ `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy token** (chỉ hiển thị một lần!)

### **Bước 2: Push Repo Lên GitHub**

```bash
cd d:\blockchain
git remote set-url origin https://YOUR-USERNAME:YOUR-TOKEN@github.com/YOUR-USERNAME/lai-vung-blockchain.git
git push -u origin main
```

### **Bước 3: Deploy Trên Render**

1. Vào https://render.com
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect a repository"**
4. Tìm & chọn repo `lai-vung-blockchain`
5. Cấu hình:
   - **Name**: `lai-vung-network`
   - **Environment**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `python run.py`
   - **Instance Type**: Free
   - **Environment Variables** (add mới):
     - Key: `GIT_USERNAME`
     - Value: `Render Blockchain` (hoặc tên tùy ý)
     - Key: `GIT_EMAIL`
     - Value: `blockchain@render.com`
     - Key: `GIT_TOKEN`
     - Value: `YOUR-PERSONAL-ACCESS-TOKEN` (paste token đã copy)

6. Click **"Create Web Service"**
7. Chờ deploy (~2-3 phút)

---

## 🔐 Cấu Hình Git Token Trên Render (Tự Động)

Khi ứng dụng khởi động trên Render:
1. `run.py` sẽ gọi `setup_git_config()`
2. Git config được thiết lập với tên & email
3. Khi có blockchain update → auto-commit → push

> ⚠️ **Lưu ý**: Token không được lưu trực tiếp trong code, mà từ environment variables

---

## 🧪 Test Locally

### Kiểm Tra Auto-Commit Hoạt Động

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate

# 2. Run app
python run.py

# 3. Mở browser: http://localhost:8000
# 4. Thêm một lô sản phẩm mới

# 5. Kiểm tra git log
git log --oneline -5
# Sẽ thấy: 🔗 Auto-commit blockchain update: ...
```

---

## 📊 Monitoring Blockchain Updates

### Xem Lịch Sử Blockchain Trên GitHub

```bash
# Xem 10 lần cập nhật gần đây nhất
git log --oneline -10 -- blockchain_ledger.json
```

### Xem Thay Đổi Cụ Thể

```bash
# So sánh blockchain giữa 2 commits
git diff COMMIT1 COMMIT2 -- blockchain_ledger.json
```

### Khôi Phục Từ Phiên Bản Cũ

```bash
# Khôi phục blockchain từ 5 commits trước
git checkout HEAD~5 -- blockchain_ledger.json
git add blockchain_ledger.json
git commit -m "Restore blockchain from backup"
git push
```

---

## ⚠️ Lưu Ý Quan Trọng

### Tốc Độ Commit
- Mỗi giao dịch = 1 commit git
- Nếu có **100 giao dịch/phút** → **100 commits/phút**
- Có thể làm git history rất lớn

**Giải pháp**: Nếu cần optimize, có thể:
- Batch commits mỗi 5-10 phút
- Dùng MongoDB (nếu muốn performance cao hơn)
- Squash commits theo tuần

### Giới Hạn GitHub
- GitHub free: không giới hạn repo private/public
- Không giới hạn commits
- Dung lượng: ~1GB (OK cho blockchain)

### Kích Thước File
- blockchain_ledger.json hiện tại: ~50KB
- Ước tính lớn nhất: 10-50MB (tùy lượng giao dịch)

---

## 🚀 Upgrade Sang MongoDB (Optional)

Nếu tương lai cần performance cao hơn:

1. Dùng **MongoDB Atlas** (free tier: 512MB)
2. Thay thế SQLite (blockchain_trace.db)
3. Vẫn keep git auto-commit cho blockchain history

---

## 📞 Troubleshooting

### ❌ Git push failed: "Authentication failed"
**Giải pháp**: Check token trên Render environment variables
```bash
# Trên Render logs, sẽ thấy:
[Git Warning] Không thể commit: ...
```

### ❌ Too many commits in git history
**Giải pháp**: Squash history
```bash
git rebase -i HEAD~100  # Gom 100 commits thành 1
git push -f origin main
```

### ❌ blockchain_ledger.json still getting deleted
**Kiểm tra**:
1. `blockchain_ledger.json` có trong `.gitignore` không?
   ```bash
   git check-ignore blockchain_ledger.json
   # Không output = không ignored ✅
   ```
2. File đã commit chưa?
   ```bash
   git ls-files blockchain_ledger.json
   # Có output = đã tracked ✅
   ```

---

## 📚 API Docs Git Helper

### `auto_commit_blockchain(filename, cwd)`
Tự động commit blockchain vào git
- **filename**: tên file (default: `blockchain_ledger.json`)
- **cwd**: working directory
- **Return**: `(success: bool, message: str)`

### `setup_git_config(cwd)`
Cấu hình git user (email, name)
- Gọi tự động lúc startup

### `get_blockchain_history(filename, max_commits)`
Lấy lịch sử commits của blockchain
- **Return**: List of commit messages

---

## ✅ Checklist Deploy

- [ ] GitHub token tạo & copy
- [ ] Repo pushed lên GitHub
- [ ] Render config đầy đủ (tất cả env vars)
- [ ] Build & Deploy thành công
- [ ] Test add product → xem git log
- [ ] blockchain_ledger.json commit với đúng message

---

**Bây giờ, dữ liệu blockchain của bạn sẽ lưu vĩnh viễn! 🎉**
