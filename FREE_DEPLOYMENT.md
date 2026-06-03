# 🆓 Deploy Miễn Phí - Hướng Dẫn Nhanh

## **Render (⭐ Khuyến Khích)**

### **Setup (5 phút)**

1. **Tạo GitHub Repo** (nếu chưa có)
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR-USERNAME/lai-vung-blockchain.git
   git push -u origin main
   ```

2. **Vào [render.com](https://render.com)**
   - Click "New +" → "Web Service"
   - Click "Connect a repository"
   - Chọn repo `lai-vung-blockchain`
   - Nhấn "Connect"

3. **Cấu Hình Deploy**
   - **Name**: `lai-vung-network`
   - **Environment**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `python run.py`
   - **Instance Type**: Free
   - Click "Create Web Service"

4. **Đợi Deploy** (~2-3 phút)
   - Xem logs xuất hiện
   - Khi xong, nhấn URL ở trên cùng

✅ **Done!** URL có dạng: `https://lai-vung-network-xxxx.onrender.com`

**Nhược Điểm:**
- App tự động sleep sau 15 phút không hoạt động (wake up mất 30s)
- Vào `https://dashboard.render.com` → "Keep Alive" để ngăn auto-sleep (chỉ free)

---

## **Replit (Rất Dễ - Không Cần GitHub)**

### **Setup (3 phút)**

1. **Vào [replit.com](https://replit.com)**
2. **Click "Create Repl"** → "Import from GitHub/URL"
   - Dán: `https://github.com/YOUR-USERNAME/lai-vung-blockchain.git`
   - Hoặc upload `.zip` file

3. **File `.replit` đã có sẵn** - chỉ cần click "Run" ▶️

4. **Lấy URL**
   - Xem mục "Webview" bên phải
   - URL có dạng: `https://lai-vung-blockchain.YOUR-USERNAME.repl.co`

✅ **Done!** Hỗ trợ tư vấn & collaboration

**Nhược Điểm:**
- Code công khai (trừ khi upgrade)
- Performance hạn chế

---

## **Railway.app (Miễn Phí + Nâng Cao)**

### **Setup (5 phút)**

1. **Vào [railway.app](https://railway.app)**
2. **Login bằng GitHub**
3. **Click "New Project"** → "Deploy from GitHub repo"
4. **Chọn repo** `lai-vung-blockchain`

5. **Add Environment Variables**
   - Click "Variables"
   - Thêm: `PORT = 8080`

6. **Deploy tự động** 🚀

**URL:** `https://your-project.railway.app`

---

## **So Sánh**

| Platform | Cost | Setup | Sleep | Uptime | Recommend |
|----------|------|-------|-------|--------|-----------|
| **Render** | Miễn phí | 5 min | 15 min | 99% | ⭐⭐⭐ |
| **Replit** | Miễn phí | 3 min | Không | 95% | ⭐⭐ |
| **Railway** | Miễn phí | 5 min | Không | 99.9% | ⭐⭐⭐ |
| **PythonAnywhere** | Miễn phí | 10 min | Không | 99% | ⭐⭐ |

---

## **Cách Giữ App Awake 24/7 (Render)**

Nếu muốn app **không bao giờ sleep**, bạn có thể dùng **Uptimerobot** (miễn phí):

1. Vào [uptimerobot.com](https://uptimerobot.com)
2. **Add Monitor** → "HTTP(s)" 
3. Nhập URL: `https://lai-vung-network-xxxx.onrender.com`
4. **Frequency**: Mỗi 5 phút check 1 lần

Cách này sẽ auto-ping app mỗi 5 phút → app không bao giờ sleep ✅

---

## **Khuyến Nghị (Miễn Phí + Tốt Nhất)**

**Render + UptimeRobot = 24/7 Miễn Phí**
1. Deploy lên Render
2. Setup UptimeRobot để keep-alive
3. **Kết quả:** App chạy 24/7 hoàn toàn miễn phí ✅

---

## **Nếu Muốn VPS Rẻ**

Nếu sau này muốn performance tốt hơn:
- **DigitalOcean Droplet**: $6/tháng (~180K VNĐ) - VPS
- **Linode**: $5/tháng - VPS
- **Hetzner**: €3/tháng (~80K VNĐ) - VPS rất rẻ

Deploy trên VPS thì cần SSH + Linux knowledge, nhưng **full control & performance tốt**.

---

## **Tóm Tắt: Bước Nhanh Nhất**

```bash
# 1. Tạo GitHub Repo
git init
git add .
git commit -m "Initial"
git push -u origin main

# 2. Vào render.com → New Web Service
# 3. Connect GitHub repo
# 4. Deploy tự động → Có URL công khai
# 5. (Optional) Thêm UptimeRobot để keep-alive
```

**Đã xong! App chạy 24/7 miễn phí** 🎉

