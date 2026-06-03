# 📦 Hướng Dẫn Deploy Lên Google Cloud

## **Chuẩn Bị**

### **1. Cài Đặt Google Cloud CLI**
- Windows: Download từ https://cloud.google.com/sdk/docs/install
- Hoặc dùng PowerShell:
```powershell
(New-Object System.Net.ServicePointManager).SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::Tls12
Invoke-WebRequest https://sdk.cloud.google.com | powershell
```

### **2. Đăng Nhập Google Cloud**
```bash
gcloud auth login
```
- Sẽ mở trình duyệt để bạn chọn tài khoản Google
- Nếu chưa có Google Cloud Account, tạo tại https://cloud.google.com

### **3. Tạo Project Trên Google Cloud**

**Tùy chọn A: Dùng gcloud CLI**
```bash
gcloud projects create lai-vung-network --name="Lai Vung Trace Network"
gcloud config set project lai-vung-network
```

**Tùy chọn B: Dùng Google Cloud Console**
1. Mở https://console.cloud.google.com
2. Click "New Project"
3. Đặt tên: `Lai Vung Trace Network`
4. Copy Project ID (cái bạn sẽ dùng trong terminal)

### **4. Enable APIs Cần Thiết**
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

### **5. (Tuỳ chọn) Cấu Hình Docker Registry**
```bash
gcloud auth configure-docker
```

---

## **Deploy Lên Cloud Run**

### **Option 1: Deploy Trực Tiếp (Dễ nhất)**
Chạy lệnh từ folder gốc `d:\blockchain`:

```bash
gcloud run deploy lai-vung-network `
  --source . `
  --platform managed `
  --region asia-southeast1 `
  --allow-unauthenticated
```

**Giải Thích:**
- `--source .` - Deploy từ thư mục hiện tại
- `--region asia-southeast1` - Khu vực Singapore (gần Việt Nam)
- `--allow-unauthenticated` - Cho phép ai cũng truy cập (không cần authentication)

Kết quả sẽ cho bạn **URL công khai**, ví dụ:
```
Service URL: https://lai-vung-network-xxxxx.a.run.app
```

### **Option 2: Deploy Từ Artifact Registry (Nâng Cao)**

**2.1 Tạo Artifact Repository:**
```bash
gcloud artifacts repositories create blockchain-repo `
  --repository-format=docker `
  --location=asia-southeast1 `
  --description="Lai Vung Blockchain"
```

**2.2 Build & Push Image:**
```bash
$PROJECT_ID = (gcloud config get-value project)
$IMAGE_URL = "asia-southeast1-docker.pkg.dev/$PROJECT_ID/blockchain-repo/lai-vung-network"

gcloud builds submit --tag $IMAGE_URL
```

**2.3 Deploy từ Image:**
```bash
gcloud run deploy lai-vung-network `
  --image $IMAGE_URL `
  --platform managed `
  --region asia-southeast1 `
  --memory 1Gi `
  --allow-unauthenticated
```

---

## **Xử Lý SQLite Persistence**

⚠️ **Lưu Ý:** Cloud Run có ephemeral filesystem (bị xóa khi restart). Để dữ liệu không bị mất:

### **Option 1: Dùng Cloud Storage (Khuyến Khích)**
Cập nhật `app/database.py` để dùng Cloud Storage:

```python
from google.cloud import storage
import os

# Initialize Cloud Storage
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "lai-vung-ledger")
client = storage.Client()
bucket = client.bucket(BUCKET_NAME)

# Download DB khi start
blob = bucket.blob("blockchain_ledger.json")
if blob.exists():
    blob.download_to_filename("blockchain_ledger.json")

# Upload DB khi update
def sync_to_storage():
    blob = bucket.blob("blockchain_ledger.json")
    blob.upload_from_filename("blockchain_ledger.json")
```

Tạo bucket:
```bash
gsutil mb gs://lai-vung-ledger
```

### **Option 2: Dùng Cloud Firestore**
Thay vì SQLite, dùng Firestore (NoSQL database miễn phí).

### **Option 3: Dùng Cloud SQL**
Dùng MySQL/PostgreSQL quản lý trên cloud.

---

## **Cấu Hình Môi Trường (Environment Variables)**

Tạo file `app.yaml` (cho Cloud Run):

```yaml
runtime: python311

env: standard

env_variables:
  GCS_BUCKET_NAME: "lai-vung-ledger"
  PORT: "8000"

handlers:
- url: /.*
  script: auto
```

---

## **Kiểm Tra Status**

```bash
# Xem tất cả deployments
gcloud run services list

# Xem logs
gcloud run services describe lai-vung-network --region asia-southeast1

# Theo dõi logs real-time
gcloud run services logs read lai-vung-network --region asia-southeast1 --limit 50 --follow
```

---

## **Costs & Pricing**

### **Cloud Run Miễn Phí (Free Tier):**
- 2 triệu requests/tháng
- 360,000 GB-seconds compute/tháng (≈ 40 instance chạy 24/7)

### **Chi Phí Nếu Vượt:**
- ~$0.00002400 / request (rất rẻ)
- ~$0.00001667 / GB-second

---

## **Custom Domain (Tuỳ Chọn)**

Để dùng domain riêng thay vì `a.run.app`:

1. Mua domain (Namecheap, GoDaddy, v.v.)
2. Setup DNS pointing tới Cloud Run
3. Cấu hình SSL certificate (tự động)

```bash
gcloud run domain-mappings create --service=lai-vung-network --domain=yourdomain.com
```

---

## **Troubleshooting**

### **Lỗi: "Docker build failed"**
- Check `requirements.txt` có tất cả dependencies?
- Check `Dockerfile` valid?

### **Lỗi: "Permission denied"**
```bash
gcloud projects get-iam-policy $(gcloud config get-value project)
```

### **Database không persistent**
- Implement Cloud Storage sync (xem phần trên)

---

## **Commands Tóm Tắt**

```bash
# 1. Login
gcloud auth login

# 2. Set project
gcloud config set project YOUR-PROJECT-ID

# 3. Deploy
gcloud run deploy lai-vung-network --source . --platform managed --region asia-southeast1 --allow-unauthenticated

# 4. Mở URL
gcloud run services describe lai-vung-network --region asia-southeast1 --format='value(status.url)'
```

---

## **Alternatives ngoài Google Cloud**

- **Vercel** (dễ nhất, chỉ 1 click deploy, free)
- **Railway** (rất dễ, UI tốt)
- **Render** (free tier tốt)
- **PythonAnywhere** (chuyên Python)
- **AWS Elastic Beanstalk** (phức tạp hơn nhưng mạnh)

