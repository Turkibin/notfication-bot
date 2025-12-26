@echo off
chcp 65001 >nul
echo 🚀 بدء النشر التلقائي...
echo.

python auto_deploy.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ تم النشر بنجاح!
) else (
    echo.
    echo ❌ فشل النشر. تحقق من الأخطاء أعلاه.
)

pause

