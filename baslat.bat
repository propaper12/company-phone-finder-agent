@echo off
chcp 65001 >nul
title 10K Şirket Telefon Agent
color 0B

echo [1/2] Gerekli paketler kontrol ediliyor...
pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/2] Sunucu başlatılıyor...
timeout /t 2 >nul
start http://127.0.0.1:8000

python server.py
pause
