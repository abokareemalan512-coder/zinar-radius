"""
🔐 زنار — نقطة دخول WSGI لـ Render.com / Gunicorn
الاستخدام: gunicorn -w 2 -b 0.0.0.0:$PORT wsgi:app
"""

import os
import sys

# إضافة مجلد المشروع
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ════════════════════════════════════════════
#  استخراج القوالب والملفات تلقائياً
# ════════════════════════════════════════════
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
if not os.path.exists(TEMPLATE_DIR) or not os.listdir(TEMPLATE_DIR):
    print('📦 مجلد القوالب فارغ أو غير موجود — جاري الاستخراج...')
    try:
        from extract_files import extract
        extract()
    except Exception as e:
        print(f'⚠️ تعذر استخراج الملفات: {e}')
else:
    print('✅ مجلد القوالب موجود')

# ════════════════════════════════════════════
#  تعيين مسار قاعدة البيانات بشكل مطلق
# ════════════════════════════════════════════
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

# ════════════════════════════════════════════
#  استيراد التطبيق مباشرة من app.py
# ════════════════════════════════════════════
from app import app, db

# تأكد إن SECRET_KEY موجود
if not os.environ.get('ZINAR_SECRET_KEY'):
    app.config['SECRET_KEY'] = 'zinar-radius-secret-key-2024-production'

# ════════════════════════════════════════════
#  تهيئة قاعدة البيانات + إنشاء المدير
# ════════════════════════════════════════════
with app.app_context():
    db.create_all()
    from app import Admin
    if not Admin.query.filter_by(username='admin').first():
        a = Admin(username='admin')
        a.set_password('admin')
        db.session.add(a)
        db.session.commit()
        print('✅ تم إنشاء حساب المدير الافتراضي (admin/admin)')
    else:
        print('✅ حساب المدير موجود بالفعل')
    print('✅ قاعدة البيانات جاهزة')

print('✅ زنار جاهز للاستقبال على WSGI')