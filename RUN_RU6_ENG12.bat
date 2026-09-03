@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ==========================================================
echo   ГЕНЕРАЦИЯ: 12 УНИКОВ RU + 24 УНИКА ENG (ADVANCED UNIQ)
echo ==========================================================
echo.
echo   Исходники : input\RU.mp4 и input\ENG.mp4
echo   Результат : output\RU\ и output\ENG\
echo.

python batch_run_ru_eng.py
echo.
pause
