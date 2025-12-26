#!/usr/bin/env python3
"""
Auto-deploy script - ينشر التعديلات تلقائياً إلى Railway
"""
import os
import sys
import subprocess

def run_git_command(cmd_list):
    """تنفيذ أمر git مباشرة بدون shell"""
    try:
        # استخدام subprocess.run مع list بدلاً من shell=True
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.stdout:
            print(result.stdout.strip())
        if result.stderr and result.returncode != 0:
            print(f"⚠️ {result.stderr.strip()}", file=sys.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ خطأ: {e}", file=sys.stderr)
        return False

def main():
    print("🚀 بدء عملية النشر التلقائي...\n")
    
    # التحقق من وجود git repository
    if not os.path.exists('.git'):
        print("❌ هذا المجلد ليس git repository!")
        print("💡 تأكد من أنك في مجلد المشروع الصحيح")
        return False
    
    # التحقق من وجود ملفات للتعديل
    files_to_deploy = ['bot.py', 'prayer_config.json']
    files_exist = [f for f in files_to_deploy if os.path.exists(f)]
    
    if not files_exist:
        print("⚠️ لم يتم العثور على الملفات للنشر")
        return False
    
    print(f"📝 الملفات للنشر: {', '.join(files_exist)}\n")
    
    # 1. إضافة الملفات
    print("📦 جاري إضافة الملفات...")
    add_cmd = ['git', 'add'] + files_exist
    if not run_git_command(add_cmd):
        print("❌ فشل في إضافة الملفات")
        return False
    
    # 2. Commit
    print("\n💾 جاري حفظ التعديلات...")
    commit_msg = "Auto-deploy: Add greeting reply and fix config"
    commit_cmd = ['git', 'commit', '-m', commit_msg]
    if not run_git_command(commit_cmd):
        print("⚠️ لا توجد تعديلات جديدة أو تم الحفظ مسبقاً")
        # لا نوقف العملية هنا، ربما الملفات محفوظة بالفعل
    
    # 3. Push
    print("\n⬆️ جاري الرفع إلى Railway...")
    push_cmd = ['git', 'push']
    if not run_git_command(push_cmd):
        print("\n❌ فشل في الرفع!")
        print("\n💡 الأسباب المحتملة:")
        print("   1. لا يوجد remote repository")
        print("   2. لم يتم تسجيل الدخول إلى Git")
        print("   3. مشكلة في الاتصال")
        print("\n🔧 الحل:")
        print("   - تأكد من إعداد git remote: git remote -v")
        print("   - أو ارفع الملفات يدوياً من Railway Dashboard")
        return False
    
    print("\n✅ تم النشر بنجاح!")
    print("🔄 Railway سيبدأ النشر التلقائي قريباً...")
    print("⏳ انتظر دقيقة أو دقيقتين حتى يكتمل النشر")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

