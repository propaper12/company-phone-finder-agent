@echo off
chcp 65001 >nul
title 10K Şirket Telefon & AI İstihbarat Agent - Otomatik Kurulum ve Başlatıcı
color 0B

echo ===============================================================================
echo     ⚡ 10K ŞİRKET TELEFON & AI İSTİHBARAT AGENT (React & Python)
echo ===============================================================================
echo.
echo [1/3] Python kontrol ediliyor...

where python >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [HATA] Bilgisayarınızda Python yüklü bulunamadı!
    echo Lütfen https://www.python.org/downloads/ adresinden Python indirip kurun.
    echo KURARKEN "Add Python to PATH" KUTUCUĞUNU İŞARETLEMEYİ UNUTMAYIN!
    echo.
    pause
    exit /b
)

echo [OK] Python bulundu.
echo.
echo [2/3] Gerekli kütüphaneler kontrol ediliyor ve yükleniyor...
echo (Bu işlem ilk açılışta 15-30 saniye sürebilir, lütfen bekleyin...)
echo.

pip install -r requirements.txt --quiet --disable-pip-version-check

echo [OK] Tüm kütüphaneler hazır!
echo.
echo [3/3] Sunucu başlatılıyor ve tarayıcı açılıyor...
echo.
echo ===============================================================================
echo     🚀 Sistem Hazır! 
echo     🌐 Adres: http://127.0.0.1:8000
echo     (Pencereyi kapatırsanız sistem durur. Simge durumuna küçültebilirsiniz.)
echo ===============================================================================
echo.

timeout /t 2 >nul
start http://127.0.0.1:8000

python server.py
pause
