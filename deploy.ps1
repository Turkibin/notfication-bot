# Auto-deploy script for Railway
Write-Host "🚀 بدء عملية النشر التلقائي..." -ForegroundColor Cyan
Write-Host ""

# Run the Python script
python auto_deploy.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ تم النشر بنجاح!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ فشل النشر. تحقق من الأخطاء أعلاه." -ForegroundColor Red
}

Read-Host "اضغط Enter للإغلاق"

