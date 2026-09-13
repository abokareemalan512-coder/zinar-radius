# 🔐 زنار v2 — دليل النشر

## الإصلاحات في الإصدار 2
- ✅ إصلاح حرج: إضافة `check_password()` لنموذج RadUser (كان يسبب انهيار بوابة المستخدم)
- ✅ تخزين كلمة المرور مشفّرة + نسخة نصية لـ FreeRADIUS
- ✅ صفحة إعدادات المدير الجديدة (`/settings`)
- ✅ خريطة الشبكة الجديدة (`/network-map`)
- ✅ إضافة روابط الشريط الجانبي الجديدة

## النشر السريع على Render.com (مجاني)

1. ارفع المشروع إلى GitHub
2. اذهب إلى https://render.com وأنشئ حساب
3. اضغط **New → Web Service**
4. اربط مستودع GitHub
5. الإعدادات:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment Variables:**
     - `ZINAR_SECRET_KEY` = مفتاح سري عشوائي
     - `DATABASE_URL` = sqlite:///zinar.db
6. اضغط **Create Web Service**

الرابط سيكون: `https://zinar-xxxx.onrender.com`

## النشر بـ Docker

```bash
docker-compose up -d
```

## النشر على VPS

```bash
chmod +x deploy-vps.sh
./deploy-vps.sh
```

## بيانات الدخول الافتراضية
- اسم المستخدم: `admin`
- كلمة المرور: `admin`

⚠️ غيّر كلمة المرور فور تسجيل الدخول من صفحة الإعدادات!
