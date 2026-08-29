@echo off
chcp 65001 > nul
cd /d "%~dp0\.."

echo ===================================================
echo   Очистка папок input\ и output\
echo ===================================================
echo.

set /p CONFIRM="Вы уверены, что хотите удалить все файлы из input\ и output\? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo [ОТМЕНА] Очистка отменена пользователем.
    echo.
    pause
    exit /b 0
)

echo.
if exist "input\" (
    del /q /f /s "input\*.*" 2>nul
    for /d %%p in ("input\*") do rmdir /s /q "%%p" 2>nul
    echo [✓] Папка input\ очищена.
) else (
    mkdir "input"
    echo [✓] Папка input\ создана.
)

if exist "output\" (
    del /q /f /s "output\*.*" 2>nul
    for /d %%p in ("output\*") do rmdir /s /q "%%p" 2>nul
    echo [✓] Папка output\ очищена.
) else (
    mkdir "output"
    echo [✓] Папка output\ создана.
)

echo.
echo [ГОТОВО] Все файлы в input\ и output\ успешно удалены!
echo.
pause
