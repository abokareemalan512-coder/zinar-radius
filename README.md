# 🔐 زنار (Zinar) — نظام RADIUS لإدارة مستخدمي ميكروتيك

**Zinar** هو نظام متكامل لإدارة مستخدمي RADIUS يدعم ميكروتيك، مع واجهة عربية كاملة.

🌐 **الموقع الرسمي:** [https://zinar.net.com](https://zinar.net.com)

## ✨ المميزات

- 🎨 واجهة عربية (RTL) بتصميم فضي أنيق (Silver/Grey)
- 👥 إدارة المستخدمين (CRUD كامل)
- 📦 باقات الإنترنت مع حدود سرعة وبيانات
- 📡 إدارة أجهزة NAS (الراوترات)
- 🔌 مصادقة Hotspot WiFi
- 📶 مصادقة PPPoE
- 💰 المحاسبة والفواتير
- 🎫 نظام الكوبونات
- 📊 التقارير المالية
- 📋 سجل الأحداث
- 💾 النسخ الاحتياطي
- 🚪 بوابة الخدمة الذاتية للمشتركين
- 🔌 قطع الجلسات عبر CoA

## 🌐 ربط النطاق المخصص (zinar.net.com)

### الطريقة أ: Cloudflare Named Tunnel (موصى بها) ⭐

بدلاً من النفق السريع الذي يعطي رابط عشوائي، استخدم نفق مُسمى:

```bash
# 1. تسجيل الدخول لـ Cloudflare
cloudflared tunnel login

# 2. إنشاء نفق باسم zinar
cloudflared tunnel create zinar

# 3. إضافة سجل DNS
cloudflared tunnel route dns zinar zinar.net.com

# 4. تشغيل النفق مع الإعدادات
cloudflared tunnel --config cloudflared-zinar.yml run zinar
```

> ملف الإعدادات `cloudflared-zinar.yml` مُضمّن مع المشروع.
> فقط استبدل `<YOUR_TUNNEL_ID_HERE>` بالمعرف الذي ستحصل عليه.

### الطريقة ب: Nginx Reverse Proxy

إذا كان النطاق يشير مباشرة لخادمك:

```bash
# 1. تأكد أن نطاق zinar.net.com يشير لـ IP السيرفر (سجل A)
# 2. انسخ إعدادات Nginx
sudo cp nginx-zinar.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/nginx-zinar.conf /etc/nginx/sites-enabled/

# 3. اختبر وأعد التحميل
sudo nginx -t && sudo systemctl reload nginx

# 4. أضف شهادة SSL مجانية
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d zinar.net.com
```

> ملف الإعدادات `nginx-zinar.conf` مُضمّن مع المشروع.

## 🚀 طرق النشر

### الطريقة 1: Docker (الأسهل) ⭐

```bash
bash deploy-docker.sh
```

### الطريقة 2: VPS بنقرة واحدة

```bash
bash deploy-vps.sh
```

### الطريقة 3: التثبيت كخدمة systemd

```bash
sudo bash install.sh
```

### الطريقة 4: Render.com (مجاني)

1. ارفع المشروع إلى GitHub
2. اربطه بـ Render.com
3. سيتم النشر تلقائياً باستخدام render.yaml

### الطريقة 5: يدوي

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

## 🔑 بيانات الدخول الافتراضية

| الحقل | القيمة |
|-------|--------|
| اسم المستخدم | admin |
| كلمة المرور | admin |

⚠️ **غيّر كلمة المرور بعد أول دخول!**

## ⚙️ متغيرات البيئة

| المتغير | الافتراضي | الوصف |
|---------|-----------|--------|
| ZINAR_PORT | 1892 | منفذ الخادم |
| ZINAR_HOST | 0.0.0.0 | عنوان الربط |
| ZINAR_PREFIX | (فارغ) | المسار الفرعي |
| ZINAR_DEBUG | 0 | وضع التصحيح |
| ZINAR_SECRET_KEY | (مفتاح افتراضي) | مفتاح التشفير |
| DATABASE_URL | sqlite:///zinar.db | رابط قاعدة البيانات |

## 📡 إعدادات RADIUS

| الخدمة | المنفذ |
|--------|--------|
| Authentication | 1812 |
| Accounting | 1813 |
| CoA | 3799 |

## 🎨 ألوان التصميم (Silver/Grey)

| العنصر | اللون | الكود |
|--------|-------|-------|
| الأساسي (Primary) | فضي | #9CA3AF |
| الأساسي الداكن | فضي داكن | #6B7280 |
| الأساسي الفاتح | فضي فاتح | #D1D5DB |
| الخلفية | داكن | #111218 |
| البطاقات | رمادي داكن | #1F2028 |
| الشريط الجانبي | رمادي غامق | #161820 |
| الحدود | رمادي | #374151 |

## 🛠️ التقنيات

- **Backend**: Flask + SQLAlchemy
- **Frontend**: Bootstrap 5 RTL + Cairo Font
- **Database**: SQLite (قابل للتحويل لـ PostgreSQL/MySQL)
- **Auth**: Flask-Bcrypt
- **Server**: Gunicorn
- **Tunnel**: Cloudflare (للوصول العام)

## 📄 الترخيص

MIT License
