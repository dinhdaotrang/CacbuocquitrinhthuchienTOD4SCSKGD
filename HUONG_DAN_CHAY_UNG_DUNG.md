# Hướng dẫn chạy ứng dụng Streamlit

## Cách chạy nhanh nhất

### Cách 1: Sử dụng file batch (Khuyến nghị)
1. Double-click vào file `run_app.bat` trong thư mục dự án
2. Ứng dụng sẽ tự động mở trong trình duyệt tại `http://localhost:8501`

### Cách 2: Sử dụng Command Prompt
```cmd
cd /d "D:\AI\Cursor\Các bước qui trình SCS-TOD4\CacbuocquitrinhthuchienTOD4SCSKGD"
python -m streamlit run app.py
```

### Cách 3: Sử dụng PowerShell
```powershell
cd "D:\AI\Cursor\Các bước qui trình SCS-TOD4\CacbuocquitrinhthuchienTOD4SCSKGD"
streamlit run app.py
```

## Thông tin ứng dụng

- **URL mặc định**: http://localhost:8501
- **Port**: 8501 (có thể thay đổi nếu port này đã được sử dụng)
- **File chính**: `app.py`
- **File tính năng**: `features.py`

## Dừng ứng dụng

- Nhấn `Ctrl + C` trong terminal/command prompt
- Hoặc đóng cửa sổ terminal

## Lưu ý

- Đảm bảo đã cài đặt Python và các thư viện cần thiết (xem `requirements.txt`)
- Nếu port 8501 đã được sử dụng, Streamlit sẽ tự động chọn port khác (8502, 8503, ...)
- Ứng dụng sẽ tự động reload khi bạn thay đổi code

## Cài đặt dependencies (nếu chưa có)

```bash
pip install -r requirements.txt
```

## Troubleshooting

### Lỗi "Module not found"
- Chạy: `pip install -r requirements.txt`

### Lỗi "Port already in use"
- Đóng ứng dụng Streamlit đang chạy khác
- Hoặc chỉ định port khác: `streamlit run app.py --server.port 8502`

### Lỗi encoding với đường dẫn tiếng Việt
- Sử dụng file `run_app.bat` để tránh vấn đề encoding

