@echo off
cd /d "C:\Users\pc\OneDrive\Masaüstü\jobbot"

:: Ollama AI sunucusunu arka planda başlat
start "" /MIN cmd /c "ollama run mistral"

:: Bekle ki sunucu ayağa kalksın
timeout /t 5 >nul

:: Python scriptlerini çalıştır
python sheet_test.py
if errorlevel 1 (
    echo sheet_test.py hata verdi.
    pause
    exit /b 1
)

python score_updater.py
if errorlevel 1 (
    echo score_updater.py hata verdi.
    pause
    exit /b 1
)

echo İşlem tamamlandı.
pause
