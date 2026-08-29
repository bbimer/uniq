@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ===================================================
echo   Очистка папки output\ (результаты обработки)
echo ===================================================
echo.

if exist "output\" (
    del /q /f /s "output\*.*" 2>nul
    for /d %%p in ("output\*") do rmdir /s /q "%%p" 2>nul
    echo [✓] Папка output\ успешно очищена.
) else (
    mkdir "output"
    echo [✓] Папка output\ создана.
)

echo.
pause
