# 🍊 Lai Vung Trace Network - Hệ thống Truy xuất Nguồn gốc Quýt Hồng

Dự án mẫu (Full-stack demo) hệ thống truy xuất nguồn gốc nông sản Quýt Hồng Lai Vung kết hợp các công nghệ tiên tiến **Blockchain (Sổ cái phân tán)** và **AI (Nhận diện & trích xuất giọng nói)**. 

Hệ thống được thiết kế theo kiến trúc Hybrid tối ưu: lưu trữ thông tin đầy đủ ở cơ sở dữ liệu truyền thống (SQLite) và lưu trữ mã băm bảo mật (Cryptographic Hash) kèm theo mốc sự kiện chính trên Blockchain để đối chiếu bảo mật.

---

## 🛠️ Công Nghệ Sử Dụng

1. **Backend & AI Engine (Bộ não):**
   - **FastAPI (Python):** Xử lý bất đồng bộ (async), tốc độ phản hồi microsecond, cung cấp RESTful APIs.
   - **AI Speech-to-Text Parsing Pipeline:** Mô phỏng quy trình Whisper Speech Recognition kết hợp GPT model bóc tách ngôn ngữ tự nhiên tiếng Việt của nông dân thành cấu trúc JSON chuẩn.
   
2. **Blockchain Ledger (Tính Minh Bạch):**
   - **Python Blockchain Engine:** Bản dựng Blockchain hoàn chỉnh hỗ trợ cấu trúc Block liên kết, mã hóa SHA-256, cơ chế đào khối Proof-of-Work (mô phỏng Nonce tìm kiếm độ khó hợp lệ) và kiểm tra tính toàn vẹn chuỗi.
   - **JSON Persistence Ledger:** Sổ cái blockchain lưu trữ lâu dài dưới dạng file JSON (`blockchain_ledger.json`).

3. **Frontend SPA (Giao diện người dùng):**
   - **HTML5 & Vanilla CSS/JS:** Sử dụng phong cách thiết kế hiện đại Glassmorphism, tông màu cam quýt đặc trưng, responsive tốt trên các thiết bị.
   - **QR Code Generator:** Tích hợp sinh mã QR Code động để dán lên thùng quýt hoặc dán tem trên sản phẩm.
   - **Hacker Simulator Lab:** Cho phép giả lập tấn công sửa đổi cơ sở dữ liệu SQLite trực tiếp và xem Blockchain phát hiện sự thay đổi thông tin này như thế nào.

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
d:/blockchain/
│
├── app/
│   ├── __init__.py
│   ├── ai_helper.py     # Xử lý ngôn ngữ tự nhiên, bóc tách text tiếng Việt sang JSON
│   ├── blockchain.py    # Cấu trúc Blockchain, SHA-256 Hashing, Proof-of-Work
│   ├── database.py      # Kết nối SQLite, lưu trữ chi tiết vòng đời lô nông sản
│   └── main.py          # FastAPI App chính & định nghĩa các Route API
│
├── static/              # Các file tĩnh phục vụ Frontend
│   ├── css/
│   │   └── styles.css   # Giao diện Premium, hiệu ứng Timeline, Blockchain Explorer
│   ├── js/
│   │   └── app.js       # Xử lý Client side: Call APIs, Mic Audio, sinh QR Code
│   └── index.html       # Giao diện Single Page Application (SPA)
│
├── requirements.txt     # Danh sách các gói thư viện Python cần cài đặt
├── run.py               # Lệnh chạy khởi động hệ thống nhanh chóng
└── README.md            # Tài liệu hướng dẫn sử dụng (File này)
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### Bước 1: Chuẩn bị môi trường
Yêu cầu hệ thống đã cài đặt sẵn **Python (phiên bản >= 3.8)**.

### Bước 2: Cài đặt các thư viện cần thiết
Mở terminal tại thư mục dự án `d:\blockchain` và chạy lệnh sau để cài đặt các package:

```bash
pip install -r requirements.txt
```

### Bước 3: Khởi chạy Server ứng dụng
Khởi động FastAPI backend bằng lệnh:

```bash
python run.py
```

Sau khi chạy lệnh, server sẽ hoạt động tại địa chỉ: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**. Hãy mở trình duyệt và truy cập link trên.

---

## 💡 Kịch Bản Trải Nghiệm Hệ Thống (Demo Steps)

1. **Bước 1: Khai báo gieo trồng (Farmer Tab)**
   - Chọn một trong các **Mẫu kịch bản Giọng nói tiếng Việt** bên phải (Ví dụ: "Thu hoạch lô QL-01").
   - Trợ lý AI sẽ tự động điền các thông tin (Mã lô, ngày canh tác, phân bón, thuốc BVTV, sản lượng...) vào form bên trái. Bạn cũng có thể xem Prompt mẫu mà AI đã gửi đến LLM trong phần *AI Diagnostics*.
   - Nhấn **Đăng ký Lô hàng & Đóng dấu Blockchain**. Hiệu ứng đào khối Blockchain sẽ xuất hiện và lưu dữ liệu.

2. **Bước 2: Cập nhật Vận chuyển (Transporter Tab)**
   - Chọn lô hàng vừa tạo (Ví dụ: QL-01) ở danh sách.
   - Thay đổi các thông số nhiệt độ bảo quản bằng slider (di chuyển slider để thấy màu sắc nhiệt độ biến đổi), chọn trạng thái hàng hóa.
   - Nhấn **Xác nhận Giao nhận & Lưu Blockchain**.

3. **Bước 3: Nhập kho Phân phối (Distributor Tab)**
   - Chọn lô hàng vừa vận chuyển xong.
   - Khai báo điều kiện bảo quản tại kệ hàng và ngày bắt đầu bày bán.
   - Nhấn **Xác nhận Nhập quầy & Ghi nhận Blockchain**.

4. **Bước 4: Tra cứu và Kiểm định bảo mật (Consumer Tab & Hacker Lab)**
   - Nhập mã lô hàng (Ví dụ: `QL-01`) vào ô tra cứu và bấm **Tra cứu**.
   - Sơ đồ **Timeline hành trình sản phẩm** sẽ hiển thị đầy đủ, chi tiết từ ngày trồng, phân bón đến nhiệt độ vận chuyển kèm theo dấu kiểm định **Xác thực sổ cái** màu xanh lá. Hệ thống đồng thời sinh ra **Mã QR Code động** tương thích cho việc truy vết trên nhãn mác.
   - Kéo xuống dưới cùng bên phải, mở rộng phần **Hacker Lab: Giả lập can thiệp SQL**.
   - Hãy chọn thay đổi trường dữ liệu (Ví dụ: Đổi Phân bón thành *Phân bón hóa học cực độc bị cấm*) và bấm **Chạy Giả Lập Tấn Công SQL**.
   - Hệ thống sẽ tấn công trực tiếp vào cơ sở dữ liệu SQLite. Sau khi hoàn tất, giao diện người dùng sẽ tự động tải lại thông tin tra cứu. Lúc này, mã băm thực tế tính toán từ DB sẽ lệch so với mã băm gốc lưu trên Blockchain. 
   - Huy hiệu xanh lá an toàn sẽ ngay lập tức biến mất, thay thế bằng cảnh báo nhấp nháy đỏ rực rỡ: **"CẢNH BÁO: DỮ LIỆU ĐÃ BỊ THAY ĐỔI TRÁI PHÉP!"**.

5. **Bước 5: Trình khám phá Blockchain (Blockchain Explorer Tab)**
   - Truy cập tab này để xem chuỗi khối Lai Vung Trace Network. Mỗi block chứa thông tin số thứ tự, thời gian đào, số nonce, mã băm khối hiện tại và khối trước đó, kèm danh sách chi tiết các giao dịch băm dữ liệu nông nghiệp đã diễn ra.
