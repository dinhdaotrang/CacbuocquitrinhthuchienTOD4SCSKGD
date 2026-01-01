# Ứng dụng Quy trình TOD4 - SCS

Ứng dụng web Streamlit để hiển thị và quản lý quy trình phê duyệt dự án và lựa chọn nhà đầu tư thực hiện dự án đầu tư có sử dụng đất (TOD4, SCS).

## 🚀 Tính năng

### Tính năng cơ bản
- **📊 Tổng quan quy trình**: Xem tổng quan với biểu đồ tiến độ và thống kê
- **📑 Danh sách bước**: Xem tất cả các bước trong quy trình
- **📋 Chi tiết bước**: Xem chi tiết từng bước với đầy đủ thông tin
- **🔍 Tìm kiếm**: Tìm kiếm nhanh trong nội dung quy trình
- **📈 Biểu đồ trực quan**: Timeline, Process Flow, và các biểu đồ bổ trợ

### Tính năng nâng cao
- **📁 Quản lý tài liệu**: Upload, lưu trữ và đọc tài liệu (PDF, Word, Text, Excel)
- **✅ Checklist & Trạng thái**: Theo dõi tiến độ từng bước với trạng thái (Chưa thực hiện/Đang thực hiện/Hoàn thành)
- **📊 Thanh tiến độ**: Hiển thị tiến độ tổng thể và cho phép ghi chú
- **🤖 Trợ lý AI**: Tích hợp OpenAI để hỏi đáp, tóm tắt và hướng dẫn về quy trình

## 📦 Cài đặt

1. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

2. Đảm bảo file CSV `TOD4_TIẾN ĐỘ VÀ CÁC BƯỚC THỰC HIỆN CV REV2.csv` nằm trong cùng thư mục với `app.py`

3. (Tùy chọn) Để sử dụng Trợ lý AI:
   - Tạo file `.env` từ `.env.example`
   - Thêm OpenAI API key: `OPENAI_API_KEY=your_api_key_here`
   - Lấy API key từ: https://platform.openai.com/api-keys

4. Chạy ứng dụng:
```bash
streamlit run app.py
```

## 📁 Cấu trúc dự án

```
.
├── app.py          # File chính của ứng dụng Streamlit
├── features.py     # Module chứa các tính năng nâng cao (biểu đồ, file, checklist, AI)
├── requirements.txt # Danh sách thư viện cần thiết
├── README.md       # File hướng dẫn
├── .env.example    # Template file cấu hình API key
├── .gitignore      # Git ignore file
├── TOD4_TIẾN ĐỘ VÀ CÁC BƯỚC THỰC HIỆN CV REV2.csv  # Dữ liệu quy trình
└── uploaded_documents/  # Thư mục lưu trữ tài liệu upload (tự động tạo)
```

## 🎯 Sử dụng

### Các trang chính:
1. **📊 Tổng quan**: Xem tổng quan quy trình với các thống kê và biểu đồ
2. **📋 Bảng tiến độ**: Xem bảng tiến độ chi tiết với khả năng xuất CSV/Excel
3. **📑 Danh sách bước**: Duyệt qua tất cả các bước trong quy trình
4. **🔍 Tìm kiếm**: Sử dụng thanh tìm kiếm để tìm nội dung cụ thể
5. **📈 Biểu đồ**: Xem các biểu đồ trực quan (Timeline, Process Flow, Pie, Line)
6. **📁 Tài liệu**: Upload và quản lý tài liệu liên quan
7. **✅ Checklist**: Theo dõi tiến độ và trạng thái thực hiện từng bước
8. **🤖 Trợ lý AI**: Hỏi đáp với AI về quy trình (cần API key)

## 📊 Dữ liệu

Ứng dụng đọc dữ liệu từ file CSV với các cột:
- STT: Mã bước/công việc
- NỘI DUNG CÔNG VIỆC: Mô tả công việc
- ĐƠN VỊ THỰC HIỆN: Đơn vị chịu trách nhiệm
- CĂN CỨ: Căn cứ pháp lý
- Thời gian: Thời gian thực hiện
- Căn cứ tiến độ: Căn cứ về tiến độ
- Ghi chú: Các ghi chú bổ sung

## 🛠️ Công nghệ

- **Streamlit**: Framework web app
- **Pandas**: Xử lý dữ liệu
- **Plotly**: Trực quan hóa dữ liệu (Timeline, Flow Chart, Pie, Line charts)
- **OpenAI API**: Trợ lý AI (tùy chọn)
- **PyPDF2**: Đọc file PDF
- **docx2python**: Đọc file Word

## 📝 Ghi chú

- Ứng dụng tự động parse và xử lý dữ liệu từ CSV
- Hỗ trợ tìm kiếm theo từ khóa
- Giao diện responsive, dễ sử dụng cho người dùng không chuyên
- Tài liệu upload được lưu trong thư mục `uploaded_documents/`
- Checklist và trạng thái được lưu trong session (tạm thời)
- Trợ lý AI sử dụng OpenAI GPT-3.5-turbo (cần API key)

## 📝 Ghi chú

- Ứng dụng tự động parse và xử lý dữ liệu từ CSV
- Hỗ trợ tìm kiếm theo từ khóa
- Giao diện responsive, dễ sử dụng cho người dùng không chuyên

