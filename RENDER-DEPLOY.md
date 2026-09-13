# 🚀 نشر زنار على Render.com — رابط دائم مجاني

## الخطوات بالتفصيل:

### ✅ الخطوة 1: إنشاء حساب GitHub
1. اذهب إلى https://github.com/signup
2. أنشئ حساب مجاني
3. أكد البريد الإلكتروني

### ✅ الخطوة 2: إنشاء مستودع GitHub
1. اذهب إلى https://github.com/new
2. اسم المستودع: `zinar-radius`
3. اختر **Private** أو **Public**
4. اضغط **Create repository**

### ✅ الخطوة 3: رفع المشروع
**الطريقة السهلة (متصفح):**
1. افتح المستودع على GitHub
2. اضغط **Add file → Upload files**
3. اسحب كل ملفات المشروع
4. اضغط **Commit changes**

**أو بالأوامر:**
```bash
cd zinar
git init
git add .
git commit -m '🔐 زنار RADIUS'
git remote add origin https://github.com/YOUR_USERNAME/zinar-radius.git
git branch -M main
git push -u origin main
```

### ✅ الخطوة 4: إنشاء حساب Render.com
1. اذهب إلى https://render.com
2. اضغط **Get Started**
3. سجّل **باستخدام GitHub** ← مهم!

### ✅ الخطوة 5: نشر المشروع
1. في لوحة Render اضغط **New → Web Service**
2. اختر مستودع `zinar-radius`
3. Render سيقرأ `render.yaml` تلقائياً
4. اسم الخدمة: `zinar-radius`
5. اختر الخطة **Free**
6. اضغط **Create Web Service**

### ✅ الخطوة 6: رابطك الدائم! 🎉
بعد 3-5 دقائق ستحصل على رابط:

```
https://zinar-radius.onrender.com
```

## ⚠️ ملاحظات مهمة:
- الخطة المجانية تُطفئ السيرفر بعد 15 دقيقة بدون زيارة
- أول زيارة بعد إطفاء تستغرق ~30 ثانية للاستيقاظ
- البيانات (SQLite) تبقى محفوظة دائماً
- لعمل 24/7 بدون توقف: خطة Starter ($7/شهر)

## بيانات الدخول:
- المستخدم: admin
- كلمة المرور: admin  
- ⚠️ غيّرها بعد أول دخول!
