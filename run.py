#!/usr/bin/env python3
"""
🔐 زنار — مشغّل خادم التطوير والاختبار
تشغيل: python3 run.py
الوصول: http://IP:PORT/
"""

import os
import sys

# إضافة مجلد المشروع
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import app, db

# ═══════════════════════════════════════════
#  إعدادات التشغيل
# ═══════════════════════════════════════════

HOST = os.environ.get('ZINAR_HOST', '0.0.0.0')
PORT = int(os.environ.get('ZINAR_PORT', '1892'))
DEBUG = os.environ.get('ZINAR_DEBUG', '0') == '1'

# ═══════════════════════════════════════════
#  تهيئة قاعدة البيانات + مستخدم المدير
# ═══════════════════════════════════════════

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

# ═══════════════════════════════════════════
#  تشغيل الخادم
# ═══════════════════════════════════════════

if __name__ == '__main__':
    url = f'http://localhost:{PORT}/'
    print()
    print('╔════════════════════════════════════════════════╗')
    print('║  🔐 زنار — نظام RADIUS لإدارة المستخدمين      ║')
    print('╠════════════════════════════════════════════════╣')
    print(f'║  المحلي:  {url}')
    print(f'║  الدخول:  admin / admin')
    print('╚════════════════════════════════════════════════╝')
    print()
    
    app.run(host=HOST, port=PORT, debug=DEBUG)
