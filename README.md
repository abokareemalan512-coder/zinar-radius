# zinar-radius
Private
# 1. إزالة أي إعدادات Git قديمة على جهازك
rm -rf .git

# 2. تهيئة المستودع من جديد
git init

# 3. إضافة جميع الملفات
git add .

# 4. حفظ التغييرات أولية
git commit -m "🔐 Initial commit - Zinar RADIUS System"

# 5. تغيير اسم الفرع إلى main
git branch -M main

# 6. ربط المشروع بمستودعك الجديد على GitHub (استبدل باسم حسابك إذا لزم الأمر)
git remote add origin https://github.com/abokareemalan512-coder/zinar-radius.git

# 7. رفع الملفات إلى GitHub بالقوة لتأكيد الرفع
git push -u origin main --force
