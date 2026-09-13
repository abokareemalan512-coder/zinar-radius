# 🔐 زنار v2 — دليل النشر خطوة بخطوة

## ✅ الإصلاحات في الإصدار 2
1. **إصلاح حرج**: إضافة `check_password()` لنموذج RadUser — كان يسبب انهيار كامل لبوابة المستخدم الذاتية
2. **تحسين أمني**: تخزين كلمة المرور مشفّرة (werkzeug hash) + نسخة نصية لـ FreeRADIUS
3. **صفحة جديدة**: إعدادات المدير (`/settings`) — تغيير كلمة المرور + الملف الشخصي
4. **صفحة جديدة**: خريطة الشبكة (`/network-map`) — طوبولوجيا بصرية للراوترات
5. **تحسين**: إضافة روابط الشريط الجانبي للصفحات الجديدة

---

## 🚀 الطريقة 1: Render.com (الأسهل — مجاني)

> النتيجة: رابط عام دائم مثل `https://zinar-radius.onrender.com`

### الخطوة 1: أنشئ مستودع GitHub
1. اذهب إلى https://github.com/new
2. اسم المستودع: `zinar-radius`
3. اختر **Private** أو **Public**
4. اضغط **Create repository**

### الخطوة 2: ارفع المشروع
فك ضغط الملف `zinar-v2.zip` في مجلد، ثم:
```bash
cd zinar-v2
git init
git add .
git commit -m "🔐 زنار v2 — Initial commit"
git remote add origin https://github.com/USERNAME/zinar-radius.git
git push -u origin main
```

### الخطوة 3: أنشئ خدمة على Render
1. اذهب إلى https://dashboard.render.com
2. اضغط **New → Web Service**
3. اربط حساب GitHub واختر مستودع `zinar-radius`
4. الإعدادات:
   | الإعداد | القيمة |
   |---|---|
   | Runtime | Python |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn -w 2 -b 0.0.0.0:$PORT run:app` |
   | Instance Type | Free |

5. في قسم **Environment Variables** أضف:
   - `ZINAR_SECRET_KEY` = اضغط **Generate** لإنشاء مفتاح عشوائي
   - `DATABASE_URL` = `sqlite:///zinar.db`

6. اضغط **Create Web Service** ✅

### الخطوة 4: انتظر النشر
- Render سيبني المشروع تلقائياً (حوالي 2-3 دقائق)
- بعد الانتهاء ستحصل على رابط مثل:
  **`https://zinar-radius-xxxx.onrender.com`** 🔗

### بيانات الدخول
- اسم المستخدم: `admin`
- كلمة المرور: `admin`

⚠️ **غيّر كلمة المرور فوراً من صفحة الإعدادات!**

---

## 🚀 الطريقة 2: Railway.app (سريع)

1. اذهب إلى https://railway.app
2. اضغط **New Project → Deploy from GitHub**
3. اختر المستودع
4. Railway سيكتشف تلقائياً أنه مشروع Python
5. أضف Environment Variables:
   - `ZINAR_SECRET_KEY` = مفتاح عشوائي
6. اضغط **Deploy**
7. الرابط: `https://zinar-radius.up.railway.app`

---

## 🚀 الطريقة 3: Docker + Cloudflare Tunnel (رابط عام دائم)

> هذه الطريقة تعطيك رابط ثابت مثل `zinar.yourdomain.com`

### المتطلبات
- سيرفر VPS (أي حجم)
- نطاق Domain

### الخطوات
```bash
# 1. فك الضغط وادخل المجلد
unzip zinar-v2.zip && cd zinar-v2

# 2. شغّل بالـ Docker
docker-compose up -d

# 3. راقب الرابط العام (Cloudflare tunnel يبدأ تلقائياً)
docker logs -f zinar-radius 2>&1 | grep trycloudflare
```

ستحصل على رابط مثل: `https://random-name.trycloudflare.com`

### لربط نطاقك الخاص:
1. أنشئ حساب على https://dash.cloudflare.com
2. اذهب إلى **Zero Trust → Networks → Tunnels**
3. أنشئ Tunnel جديد باسم `zinar`
4. اربطه بالنطاق `zinar.yourdomain.com`
5. أضف ملف الإعداد `cloudflared-zinar.yml`
6. النتيجة: **`https://zinar.yourdomain.com`** 🔗

---

## 🚀 الطريقة 4: PythonAnywhere (مجاني)

1. اذهب إلى https://www.pythonanywhere.com
2. أنشئ حساب مجاني
3. ارفع ملفات المشروع
4. افتح Bash Console:
```bash
pip install -r requirements.txt
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```
5. اذهب إلى **Web tab**:
   - Code directory: مجلد المشروع
   - WSGI file: أضف `from run import app as application`
6. الرابط: `https://username.pythonanywhere.com`

---

## 📡 ربط ميكروتيك بزنار

بعد رفع زنار على Render، اربط الراوتر:

```routeros
# على ميكروتيك
/radius add address=RENDER_URL port=1812 secret=SHARED_SECRET service=ppp
/radius add address=RENDER_URL port=1812 secret=SHARED_SECRET service=hotspot
/radius set use-radius=yes
```

> ملاحظة: لربط ميكروتيك بـ FreeRADIUS على Render تحتاج خادم FreeRADIUS يعمل بجانب زنار. راجع ملف `mikrotik_setup.rsc` للإعدادات الكاملة.

---

## 🔑 نصائح مهمة
1. **غيّر كلمة المرور الافتراضية** فور تسجيل الدخول
2. **استخدم HTTPS دائماً** — Render يوفره مجاناً
3. **اعمل نسخ احتياطي** من صفحة النسخ الاحتياطي بشكل دوري
4. **الخطة المجانية على Render** ينام السيرفر بعد 15 دقيقة عدم نشاط (يستيقظ عند الطلب الأول، يأخذ ~30 ثانية)
5. **للإنتاج** يفضل خطة Render المدفوعة ($7/شهر) أو VPS خاص
