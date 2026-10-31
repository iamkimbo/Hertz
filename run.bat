@echo off
cd /d "%~dp0"

if not exist .env if not defined GOOGLE_API_KEY (
    echo No .env file or GOOGLE_API_KEY found - you can paste the key in the app when prompted.
)

python -m streamlit run app.py
pause
