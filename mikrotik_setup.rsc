# ==============================================================
# MikroTik RouterOS Setup Script for زنار (Zinar) RADIUS System
# Server: 177.188.15.20
# Run this script on your MikroTik router
# ==============================================================

# --- إعدادات RADIUS ---
# استبدل SHARED_SECRET بنفس السر المشترك المُدخل في زنار
/radius add address=177.188.15.20 secret=SHARED_SECRET service=ppp,hotspot,dhcp timeout=3000ms
/radius incoming set accept=yes port=3799

# --- إعدادات Hotspot ---
/interface bridge add name=bridge1
/interface wireless set wlan1 ssid="Zinar-WiFi"

/ip hotspot profile add name=zinar-profile hotspot-address=10.5.5.1 dns-name=login.zinar.local \
    login-by=http-chap,http-pap html-directory=flash/hotspot use-radius=yes

/ip hotspot add name=hotspot1 interface=bridge1 profile=zinar-profile disabled=no

# صفحة تسجيل الدخول (نسخة مخصصة)
/ip hotspot walled-garden add dst-host=177.188.15.20

# --- إعدادات PPPoE ---
/interface pppoe-server server add service-name=zinar-pppoe interface=bridge1 \
    max-sessions=1000 default-profile=default one-session-per-host=yes

/ppp profile add name=zinar-pppoe use-radius=yes local-ip=10.0.0.1 \
    dns-server=8.8.8.8,8.8.4.4

/ppp aaa set use-radius=yes accounting=yes

# --- إعدادات المحاسبة ---
/radius accounting set interim-update=300s

# --- جدار الحماية ---
/ip firewall filter add chain=input protocol=udp port=3799 action=accept comment="Allow CoA from RADIUS"
/ip firewall filter add chain=input src-address=177.188.15.20 action=accept comment="Allow RADIUS Server"

# --- SNMP (اختياري للمراقبة) ---
/snmp set enabled=yes contact=admin location="Zinar Network"

# --- التحقق ---
:put "RADIUS Server: 177.188.15.20"
:put "CoA Port: 3799"
:put "Setup Complete!"

# ==============================================================
# ملاحظات مهمة:
# 1. تأكد من تغيير SHARED_SECRET بنفس القيمة المُدخلة في زنار
# 2. Hotspot يجب أن يكون صفحة الـ HTML جاهزة على الراوتر
# 3. منفذ 3799 يجب أن يكون مفتوحاً لـ CoA (قطع الاتصال عن بعد)
# 4. لفحص الاتصال: /radius monitor (اسم-السيرفر)
# ==============================================================