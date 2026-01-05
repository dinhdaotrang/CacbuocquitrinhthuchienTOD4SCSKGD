@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Đang khởi động ứng dụng Streamlit...
python -m streamlit run app.py
pause

