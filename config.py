"""
════════════════════════════════════════════════════════════
  🔐 زنار — إعدادات النظام
════════════════════════════════════════════════════════════
"""
import os

# ═════════════════════════════
#  إعدادات الخادم
# ═════════════════════════════

SERVER_IP = os.environ.get('RADIUS_SERVER_IP', '177.188.15.20')
SERVER_NAME = 'زنار'
SERVER_NAME_EN = 'Zinar'

# ═════════════════════════════
#  منافذ RADIUS
# ═════════════════════════════

RADIUS_AUTH_PORT = int(os.environ.get('RADIUS_AUTH_PORT', 1812))
RADIUS_ACCT_PORT = int(os.environ.get('RADIUS_ACCT_PORT', 1813))
RADIUS_COA_PORT = int(os.environ.get('RADIUS_COA_PORT', 3799))

# ═════════════════════════════
#  قاعدة البيانات
# ═════════════════════════════

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///zinar.db')
RADIUS_DB_URL = os.environ.get('RADIUS_DB_URL', '')

# ═════════════════════════════
#  FreeRADIUS
# ═════════════════════════════

FREERADIUS_CLIENTS_CONF = os.environ.get(
    'FREERADIUS_CLIENTS_CONF',
    '/etc/freeradius/3.0/clients.conf'
)
FREERADIUS_SERVICE = 'freeradius'

# ═════════════════════════════
#  إعدادات MikroTik
# ═════════════════════════════

MIKROTIK_VENDOR = 'Mikrotik'
MIKROTIK_VSA_ID = 14929

# سمات MikroTik الخاصة
MIKROTIK_ATTRS = {
    'RATE_LIMIT': 'Mikrotik-Rate-Limit',
    'GROUP': 'Mikrotik-Group',
    'TOTAL_LIMIT': 'Mikrotik-Total-Limit',
    'RECV_LIMIT': 'Mikrotik-Recv-Limit',
    'XMIT_LIMIT': 'Mikrotik-Xmit-Limit',
    'WIRELESS_VLAN_ID': 'Mikrotik-Wireless-VLAN-ID',
    'WIRELESS_VLAN_ID_TYPE': 'Mikrotik-Wireless-VLAN-ID-Type',
}

# ═════════════════════════════
#  أنواع المصادقة
# ═════════════════════════════

AUTH_TYPES = {
    'hotspot': {
        'label': 'WiFi Hotspot',
        'service': 'hotspot',
        'default_group': 'hotspot-users',
    },
    'pppoe': {
        'label': 'PPPoE اشتراك',
        'service': 'ppp',
        'default_group': 'pppoe-users',
    },
}

# ═════════════════════════════
#  طرق الدفع
# ═════════════════════════════

PAYMENT_METHODS = {
    'cash': 'نقدي',
    'card': 'بطاقة',
    'transfer': 'تحويل بنكي',
}

# ═════════════════════════════
#  العملة
# ═════════════════════════════

CURRENCY = 'ر.س'
CURRENCY_EN = 'SAR'

# ═════════════════════════════
#  الإعدادات الافتراضية
# ═════════════════════════════

DEFAULT_ADMIN = {
    'username': 'admin',
    'password': 'admin',
    'full_name': 'مدير النظام'
}

DEFAULT_PACKAGES = [
    {'name': 'برونزي', 'name_en': 'Bronze', 'speed_down': '2M', 'speed_up': '1M', 'price': 15, 'time_limit_days': 30},
    {'name': 'فضي', 'name_en': 'Silver', 'speed_down': '5M', 'speed_up': '2M', 'price': 30, 'time_limit_days': 30},
    {'name': 'ذهبي', 'name_en': 'Gold', 'speed_down': '10M', 'speed_up': '5M', 'price': 50, 'time_limit_days': 30},
    {'name': 'ماسي', 'name_en': 'Diamond', 'speed_down': '20M', 'speed_up': '10M', 'price': 80, 'time_limit_days': 30},
    {'name': 'يومي', 'name_en': 'Daily', 'speed_down': '5M', 'speed_up': '2M', 'price': 3, 'time_limit_days': 1, 'data_limit_gb': 2},
    {'name': 'أسبوعي', 'name_en': 'Weekly', 'speed_down': '10M', 'speed_up': '3M', 'price': 10, 'time_limit_days': 7, 'data_limit_gb': 10},
]