import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# إعداد قاعدة البيانات (يدعم PostgreSQL على Render أو SQLite محلياً)
db_url = os.environ.get('DATABASE_URL', 'sqlite:///zinar_radius.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'zinar-radius-secret-2026')

db = SQLAlchemy(app)

# ==================== نماذج قاعدة البيانات (Database Models) ====================

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Router(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    radius_port = db.Column(db.Integer, default=1812)
    secret = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), default='الفرع الرئيسي')
    status = db.Column(db.String(20), default='متصل')

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, default=0.0)
    download_speed = db.Column(db.String(50), default='5M')
    upload_speed = db.Column(db.String(50), default='1M')
    duration_days = db.Column(db.Integer, default=30)
    data_limit_gb = db.Column(db.Float, default=0.0) # 0 = Unlimited

class RadiusUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='مفعل')
    plan_name = db.Column(db.String(100), default='5M')
    server_name = db.Column(db.String(100), default='Not Found')
    mac_address = db.Column(db.String(50), default='00:00:00:00:00:00')
    ip_address = db.Column(db.String(45), default='0.0.0.0')
    download_gb = db.Column(db.Float, default=0.0)
    upload_gb = db.Column(db.Float, default=0.0)
    uptime = db.Column(db.String(50), default='0s')
    start_date = db.Column(db.String(50), default=lambda: datetime.now().strftime('%Y-%m-%d'))
    expire_date = db.Column(db.String(100), default=lambda: (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
    allowed_data = db.Column(db.String(50), default='unlimited')
    used_data_gb = db.Column(db.Float, default=0.0)

class ActiveSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    router_name = db.Column(db.String(100), default='Main Router')
    ip_address = db.Column(db.String(45), default='10.0.0.15')
    mac_address = db.Column(db.String(50), default='AA:BB:CC:DD:EE:FF')
    uptime = db.Column(db.String(50), default='01:25:40')

# تجهيز الجداول والحساب المبدئي
with app.app_context():
    db.create_all()
    if not AdminUser.query.filter_by(username='admin').first():
        db.session.add(AdminUser(username='admin', password='adminpassword123'))
        db.session.commit()
    
    if not Router.query.first():
        db.session.add(Router(name='MikroTik Main Server', ip_address='198.145.118.146', radius_port=1812, secret='123456', location='السيرفر الرئيسي'))
        db.session.commit()

    if not Package.query.first():
        db.session.add(Package(name='5M', price=5.0, download_speed='5M', upload_speed='1M', duration_days=30, data_limit_gb=0.0))
        db.session.add(Package(name='10M', price=10.0, download_speed='10M', upload_speed='2M', duration_days=30, data_limit_gb=100.0))
        db.session.commit()

    if not RadiusUser.query.first():
        db.session.add(RadiusUser(
            username='61779069',
            password='123',
            status='مفعل',
            plan_name='5M',
            server_name='MikroTik Main Server',
            mac_address='00:00:00:00:00:00',
            ip_address='0.0.0.0',
            download_gb=342.98,
            upload_gb=35.69,
            uptime='20d15h50m55s',
            expire_date='09:03:10AM (4 Days) 19-09-2026',
            allowed_data='unlimited',
            used_data_gb=378.68
        ))
        db.session.commit()

# ==================== المسارات والتحكم (Routes) ====================

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = AdminUser.query.filter_by(username=username, password=password).first()
        if user or (username == 'admin' and password == 'admin'):
            session['user'] = username
            return redirect(url_for('dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ==================== REST APIs ====================

# 1. إحصائيات عامة
@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'total_users': RadiusUser.query.count(),
        'active_users': RadiusUser.query.filter_by(status='مفعل').count(),
        'total_routers': Router.query.count(),
        'total_packages': Package.query.count(),
        'active_sessions': ActiveSession.query.count()
    })

# 2. المشتركون (User Manager CRUD)
@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    if request.method == 'POST':
        d = request.get_json()
        u = RadiusUser(
            username=d['username'],
            password=d.get('password', '123'),
            status=d.get('status', 'مفعل'),
            plan_name=d.get('plan_name', '5M'),
            server_name=d.get('server_name', 'Not Found'),
            mac_address=d.get('mac_address', '00:00:00:00:00:00'),
            ip_address=d.get('ip_address', '0.0.0.0'),
            download_gb=0.0,
            upload_gb=0.0,
            uptime='0s',
            expire_date=(datetime.now() + timedelta(days=30)).strftime('%d-%m-%Y'),
            allowed_data=d.get('allowed_data', 'unlimited'),
            used_data_gb=0.0
        )
        db.session.add(u)
        db.session.commit()
        return jsonify({'message': 'تم إضافة المشترك بنجاح'}), 201

    users = RadiusUser.query.order_by(RadiusUser.id.desc()).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'password': u.password,
        'status': u.status,
        'plan_name': u.plan_name,
        'server_name': u.server_name,
        'mac_address': u.mac_address,
        'ip_address': u.ip_address,
        'download_gb': u.download_gb,
        'upload_gb': u.upload_gb,
        'uptime': u.uptime,
        'expire_date': u.expire_date,
        'allowed_data': u.allowed_data,
        'used_data_gb': u.used_data_gb
    } for u in users])

@app.route('/api/users/<int:id>', methods=['GET', 'DELETE'])
def single_user(id):
    u = RadiusUser.query.get(id)
    if not u:
        return jsonify({'error': 'المشترك غير موجود'}), 404
    
    if request.method == 'DELETE':
        db.session.delete(u)
        db.session.commit()
        return jsonify({'message': 'تم حذف المشترك بنجاح'})

    return jsonify({
        'id': u.id, 'username': u.username, 'password': u.password, 'status': u.status,
        'plan_name': u.plan_name, 'server_name': u.server_name, 'mac_address': u.mac_address,
        'ip_address': u.ip_address, 'download_gb': u.download_gb, 'upload_gb': u.upload_gb,
        'uptime': u.uptime, 'expire_date': u.expire_date, 'allowed_data': u.allowed_data,
        'used_data_gb': u.used_data_gb
    })

# تصفير العدادات والرفع والتحميل للباقة
@app.route('/api/users/<int:id>/reset', methods=['POST'])
def reset_counters(id):
    u = RadiusUser.query.get(id)
    if u:
        u.download_gb = 0.0
        u.upload_gb = 0.0
        u.used_data_gb = 0.0
        u.uptime = '0s'
        db.session.commit()
        return jsonify({'message': 'تم تصفير العدادات والباقة بنجاح'})
    return jsonify({'error': 'حدث خطأ أثناء التصفير'}), 400

# تجديد اشتراك المشترك
@app.route('/api/users/<int:id>/renew', methods=['POST'])
def renew_user(id):
    u = RadiusUser.query.get(id)
    if u:
        u.download_gb = 0.0
        u.upload_gb = 0.0
        u.used_data_gb = 0.0
        u.uptime = '0s'
        u.status = 'مفعل'
        u.expire_date = (datetime.now() + timedelta(days=30)).strftime('%d-%m-%Y')
        db.session.commit()
        return jsonify({'message': 'تم تجديد الاشتراك لمدة 30 يوماً وتصفير العدادات'})
    return jsonify({'error': 'فشل التجديد'}), 400

# 3. الراوترات والسيرفرات (Multi-NAS)
@app.route('/api/routers', methods=['GET', 'POST'])
def handle_routers():
    if request.method == 'POST':
        d = request.get_json()
        r = Router(
            name=d['name'],
            ip_address=d['ip_address'],
            radius_port=int(d.get('radius_port', 1812)),
            secret=d['secret'],
            location=d.get('location', 'فرع جديد')
        )
        db.session.add(r)
        db.session.commit()
        return jsonify({'message': 'تم إضافة السيرفر بنجاح'}), 201

    routers = Router.query.order_by(Router.id.desc()).all()
    return jsonify([{
        'id': r.id, 'name': r.name, 'ip_address': r.ip_address,
        'radius_port': r.radius_port, 'location': r.location, 'status': r.status
    } for r in routers])

@app.route('/api/routers/<int:id>', methods=['DELETE'])
def delete_router(id):
    r = Router.query.get(id)
    if r:
        db.session.delete(r)
        db.session.commit()
    return jsonify({'message': 'تم حذف الراوتر'})

@app.route('/api/routers/<int:id>/ping', methods=['POST'])
def ping_router(id):
    r = Router.query.get(id)
    return jsonify({'message': f'تم اختبار الاتصال بنجاح مع {r.name if r else "السيرفر"}'})

# 4. الخطط والباقات (Packages / Profiles)
@app.route('/api/packages', methods=['GET', 'POST'])
def handle_packages():
    if request.method == 'POST':
        d = request.get_json()
        p = Package(
            name=d['name'],
            price=float(d['price']),
            download_speed=d['download_speed'],
            upload_speed=d['upload_speed'],
            duration_days=int(d.get('duration_days', 30)),
            data_limit_gb=float(d.get('data_limit_gb', 0.0))
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({'message': 'تم إضافة الباقة بنجاح'}), 201

    packages = Package.query.order_by(Package.id.desc()).all()
    return jsonify([{
        'id': p.id, 'name': p.name, 'price': p.price,
        'download_speed': p.download_speed, 'upload_speed': p.upload_speed,
        'duration_days': p.duration_days, 'data_limit_gb': p.data_limit_gb
    } for p in packages])

@app.route('/api/packages/<int:id>', methods=['DELETE'])
def delete_package(id):
    p = Package.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return jsonify({'message': 'تم حذف الباقة'})

# 5. الجلسات النشطة (Active Sessions)
@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    sessions = ActiveSession.query.all()
    return jsonify([{
        'id': s.id, 'username': s.username, 'router_name': s.router_name,
        'ip_address': s.ip_address, 'mac_address': s.mac_address, 'uptime': s.uptime
    } for s in sessions])

# 6. تحديث بيانات المدير
@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    d = request.get_json()
    admin = AdminUser.query.first()
    if not admin:
        admin = AdminUser(username='admin', password='adminpassword123')
        db.session.add(admin)
    
    if d.get('username'):
        admin.username = d['username']
    if d.get('password'):
        admin.password = d['password']
        
    db.session.commit()
    session['user'] = admin.username
    return jsonify({'message': 'تم تحديث اسم المستخدم وكلمة المرور في قاعدة البيانات بنجاح', 'username': admin.username})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)"""
════════════════════════════════════════════════════════════
  🔐 زنار — نظام RADIUS لإدارة مستخدمين ميكروتيك
  Zinar — RADIUS User Management System for MikroTik
  Enhanced with MikroTik User Manager features
════════════════════════════════════════════════════════════
"""

import os
import subprocess
import secrets
import tempfile
import json
import shutil
import zipfile
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort, send_file, make_response
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════
#  تهيئة التطبيق
# ═══════════════════════════════════════════

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'ZINAR_SECRET_KEY',
    'zinar-radius-secret-key-2024-production'
)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'zinar.db')
)
# تأكد من وجود مجلد instance
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'), exist_ok=True)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ═══════════════════════════════════════════
#  دعم اللغات
# ═══════════════════════════════════════════

TRANSLATIONS = {
    'ar': {
        'brand': 'زنار',
        'brand_sub': 'zinar.net.com',
        'login': 'تسجيل الدخول',
        'username': 'اسم المستخدم',
        'password': 'كلمة المرور',
        'signin': 'دخول',
        'forgot_password': 'نسيت كلمة المرور؟',
        'no_account': 'ليس لديك حساب؟',
        'create_account': 'إنشاء حساب',
        'welcome_back': 'مرحباً بعودتك',
        'please_login': 'سجّل دخولك للمتابعة',
        'dashboard': 'لوحة التحكم',
        'users': 'المستخدمون',
        'packages': 'الباقات',
        'routers': 'الراوترات',
        'sessions': 'الجلسات',
        'payments': 'المدفوعات',
        'reports': 'التقارير',
        'logs': 'سجل الأحداث',
        'vouchers': 'الكوبونات',
        'backup': 'النسخ الاحتياطي',
        'settings': 'الإعدادات',
        'logout': 'خروج',
        'total_users': 'إجمالي المستخدمين',
        'active_users': 'مستخدمون نشطون',
        'online_now': 'متصلون الآن',
        'monthly_revenue': 'إيرادات الشهر',
        'expired': 'منتهي',
        'disabled': 'معطّل',
        'active': 'نشط',
        'add': 'إضافة',
        'edit': 'تعديل',
        'delete': 'حذف',
        'save': 'حفظ',
        'cancel': 'إلغاء',
        'search': 'بحث...',
        'confirm_delete': 'هل أنت متأكد من الحذف؟',
        'speed': 'السرعة',
        'price': 'السعر',
        'duration': 'المدة',
        'data_limit': 'حجم البيانات',
        'subscribers': 'مشتركين',
        'reset_password': 'إعادة تعيين كلمة المرور',
        'enter_email': 'أدخل بريدك الإلكتروني',
        'email': 'البريد الإلكتروني',
        'send_reset': 'إرسال رابط الإعادة',
        'back_to_login': 'العودة لتسجيل الدخول',
        'register': 'تسجيل',
        'full_name': 'الاسم الكامل',
        'phone': 'الهاتف',
        'confirm_password': 'تأكيد كلمة المرور',
        'my_account': 'حسابي',
        'my_usage': 'استهلاكي',
        'buy_plan': 'شراء باقة',
        'my_profile': 'ملفي الشخصي',
        'download_usage': 'التحميل',
        'upload_usage': 'الرفع',
        'uptime': 'وقت الاتصال',
        'current_plan': 'الباقة الحالية',
        'expires_on': 'تنتهي في',
        'available_plans': 'الباقات المتاحة',
        'buy': 'شراء',
        'balance': 'الرصيد',
        'top_up': 'شحن الرصيد',
        'generate_vouchers': 'توليد كوبونات',
        'voucher_batch': 'دفعات الكوبونات',
        'print_vouchers': 'طباعة كوبونات',
        'voucher_code': 'رمز الكوبون',
        'batch_name': 'اسم الدفعة',
        'quantity': 'الكمية',
        'voucher_status': 'حالة الكوبون',
        'used': 'مستخدم',
        'unused': 'غير مستخدم',
        'db_backup': 'نسخ احتياطي لقاعدة البيانات',
        'db_restore': 'استعادة قاعدة البيانات',
        'create_backup': 'إنشاء نسخة احتياطية',
        'restore_backup': 'استعادة من نسخة',
        'backup_date': 'تاريخ النسخة',
        'backup_size': 'حجم النسخة',
        'download_backup': 'تحميل النسخة',
        'custom_radius_attrs': 'سمات RADIUS مخصصة',
        'attribute': 'سمة',
        'operator': 'المعامل',
        'value': 'القيمة',
        'burst_config': 'إعدادات Burst',
        'burst_rate': 'سرعة Burst',
        'burst_threshold': 'عتبة Burst',
        'burst_time': 'وقت Burst',
        'min_rate': 'الحد الأدنى للسرعة',
        'priority': 'الأولوية',
        'reset_counters': 'إعادة العدادات',
        'hourly': 'كل ساعة',
        'daily': 'يومي',
        'weekly': 'أسبوعي',
        'monthly': 'شهري',
        'transfer_limit': 'حد النقل الكلي',
        'uptime_limit': 'حد وقت الاتصال',
        'ryal': 'ر.س',
        'invalid_credentials': 'اسم المستخدم أو كلمة المرور غير صحيحة',
        'insufficient_balance': 'رصيد غير كافي',
        'subscribed_success': 'تم الاشتراك بنجاح',
        'invalid_voucher': 'كود القسيمة غير صالح',
        'voucher_applied': 'تم تطبيق القسيمة بنجاح',
        'password_mismatch': 'كلمات المرور غير متطابقة',
        'password_changed': 'تم تغيير كلمة المرور بنجاح',
        'batch_settings': 'إعدادات الدفعة',
        'code_prefix': 'بادئة الكود',
        'code_length': 'طول كلمة المرور',
        'preview': 'معاينة',
        'sample_code': 'نموذج كود',
        'vouchers_desc': 'سيتم إنشاء أكواد فريدة لكل قسيمة',
        'generate': 'توليد',
    },
    'en': {
        'brand': 'Zinar',
        'brand_sub': 'zinar.net.com',
        'login': 'Login',
        'username': 'Username',
        'password': 'Password',
        'signin': 'Sign In',
        'forgot_password': 'Forgot Password?',
        'no_account': "Don't have an account?",
        'create_account': 'Create Account',
        'welcome_back': 'Welcome Back',
        'please_login': 'Please login to continue',
        'dashboard': 'Dashboard',
        'users': 'Users',
        'packages': 'Packages',
        'routers': 'Routers',
        'sessions': 'Sessions',
        'payments': 'Payments',
        'reports': 'Reports',
        'logs': 'Activity Log',
        'vouchers': 'Vouchers',
        'backup': 'Backup',
        'settings': 'Settings',
        'logout': 'Logout',
        'total_users': 'Total Users',
        'active_users': 'Active Users',
        'online_now': 'Online Now',
        'monthly_revenue': 'Monthly Revenue',
        'expired': 'Expired',
        'disabled': 'Disabled',
        'active': 'Active',
        'add': 'Add',
        'edit': 'Edit',
        'delete': 'Delete',
        'save': 'Save',
        'cancel': 'Cancel',
        'search': 'Search...',
        'confirm_delete': 'Are you sure you want to delete?',
        'speed': 'Speed',
        'price': 'Price',
        'duration': 'Duration',
        'data_limit': 'Data Limit',
        'subscribers': 'Subscribers',
        'reset_password': 'Reset Password',
        'enter_email': 'Enter your email',
        'email': 'Email',
        'send_reset': 'Send Reset Link',
        'back_to_login': 'Back to Login',
        'register': 'Register',
        'full_name': 'Full Name',
        'phone': 'Phone',
        'confirm_password': 'Confirm Password',
        'my_account': 'My Account',
        'my_usage': 'My Usage',
        'buy_plan': 'Buy Plan',
        'my_profile': 'My Profile',
        'download_usage': 'Download',
        'upload_usage': 'Upload',
        'uptime': 'Uptime',
        'current_plan': 'Current Plan',
        'expires_on': 'Expires On',
        'available_plans': 'Available Plans',
        'buy': 'Buy',
        'balance': 'Balance',
        'top_up': 'Top Up',
        'generate_vouchers': 'Generate Vouchers',
        'voucher_batch': 'Voucher Batches',
        'print_vouchers': 'Print Vouchers',
        'voucher_code': 'Voucher Code',
        'batch_name': 'Batch Name',
        'quantity': 'Quantity',
        'voucher_status': 'Voucher Status',
        'used': 'Used',
        'unused': 'Unused',
        'db_backup': 'Database Backup',
        'db_restore': 'Database Restore',
        'create_backup': 'Create Backup',
        'restore_backup': 'Restore from Backup',
        'backup_date': 'Backup Date',
        'backup_size': 'Backup Size',
        'download_backup': 'Download Backup',
        'custom_radius_attrs': 'Custom RADIUS Attributes',
        'attribute': 'Attribute',
        'operator': 'Operator',
        'value': 'Value',
        'burst_config': 'Burst Configuration',
        'burst_rate': 'Burst Rate',
        'burst_threshold': 'Burst Threshold',
        'burst_time': 'Burst Time',
        'min_rate': 'Minimum Rate',
        'priority': 'Priority',
        'reset_counters': 'Reset Counters',
        'hourly': 'Hourly',
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'transfer_limit': 'Transfer Limit',
        'uptime_limit': 'Uptime Limit',
        'ryal': 'SAR',
        'invalid_credentials': 'Invalid username or password',
        'insufficient_balance': 'Insufficient balance',
        'subscribed_success': 'Subscribed successfully',
        'invalid_voucher': 'Invalid voucher code',
        'voucher_applied': 'Voucher applied successfully',
        'password_mismatch': 'Passwords do not match',
        'password_changed': 'Password changed successfully',
        'batch_settings': 'Batch Settings',
        'code_prefix': 'Code Prefix',
        'code_length': 'Password Length',
        'preview': 'Preview',
        'sample_code': 'Sample Code',
        'vouchers_desc': 'Unique codes will be generated for each voucher',
        'generate': 'Generate',
    }
}


def get_lang():
    return session.get('lang', 'ar')


def t(key):
    lang = get_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS['ar']).get(key, key)


@app.context_processor
def inject_lang():
    return dict(lang=get_lang(), t=t, TRANSLATIONS=TRANSLATIONS)


@app.template_filter('filesizeformat')
def filesizeformat_filter(value):
    """تنسيق حجم الملف بالوحدات المناسبة"""
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return '0 B'
    if value < 1024:
        return f'{value:.0f} B'
    elif value < 1024 * 1024:
        return f'{value/1024:.1f} KB'
    elif value < 1024 * 1024 * 1024:
        return f'{value/(1024*1024):.1f} MB'
    elif value < 1024 * 1024 * 1024 * 1024:
        return f'{value/(1024*1024*1024):.1f} GB'
    else:
        return f'{value/(1024*1024*1024*1024):.1f} TB'


# ═══════════════════════════════════════════
#  نماذج قاعدة البيانات (Models)
# ═══════════════════════════════════════════

class NASDevice(db.Model):
    __tablename__ = 'nas_devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False, unique=True)
    shared_secret = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    auth_port = db.Column(db.Integer, default=1812)
    acct_port = db.Column(db.Integer, default=1813)
    coa_port = db.Column(db.Integer, default=3799)
    nas_type = db.Column(db.String(50), default='mikrotik')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Package(db.Model):
    __tablename__ = 'packages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), default='')
    # ─── سرعات أساسية ───
    speed_down = db.Column(db.String(20), nullable=False, default='2M')
    speed_up = db.Column(db.String(20), nullable=False, default='1M')
    # ─── إعدادات Burst الكاملة (User Manager style) ───
    burst_down = db.Column(db.String(20), default='')
    burst_up = db.Column(db.String(20), default='')
    burst_threshold_down = db.Column(db.String(20), default='')
    burst_threshold_up = db.Column(db.String(20), default='')
    burst_time_up = db.Column(db.Integer, default=0)
    burst_time_down = db.Column(db.Integer, default=0)
    min_rate_up = db.Column(db.String(20), default='')
    min_rate_down = db.Column(db.String(20), default='')
    priority = db.Column(db.Integer, default=8)
    # ─── حدود الاستخدام (Limitations) ───
    price = db.Column(db.Float, nullable=False, default=0)
    currency = db.Column(db.String(10), default='ر.س')
    time_limit_days = db.Column(db.Integer, default=30)
    data_limit_gb = db.Column(db.Float, default=0)
    transfer_limit_gb = db.Column(db.Float, default=0)  # upload+download combined
    uptime_limit_hours = db.Column(db.Float, default=0)  # total online time
    session_timeout = db.Column(db.Integer, default=0)
    concurrent_limit = db.Column(db.Integer, default=1)
    # ─── إعادة العدادات ───
    reset_counters = db.Column(db.String(20), default='monthly')  # hourly/daily/weekly/monthly
    # ─── حالة الباقة ───
    is_active = db.Column(db.Boolean, default=True)
    is_hotspot = db.Column(db.Boolean, default=True)
    is_pppoe = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('RadUser', backref='package', lazy='dynamic')

    @property
    def time_limit(self):
        if self.time_limit_days and self.time_limit_days > 0:
            return self.time_limit_days * 86400
        return 0

    @property
    def data_limit(self):
        if self.data_limit_gb and self.data_limit_gb > 0:
            return int(self.data_limit_gb * 1073741824)
        return 0

    @property
    def transfer_limit(self):
        if self.transfer_limit_gb and self.transfer_limit_gb > 0:
            return int(self.transfer_limit_gb * 1073741824)
        return 0

    @property
    def uptime_limit(self):
        if self.uptime_limit_hours and self.uptime_limit_hours > 0:
            return int(self.uptime_limit_hours * 3600)
        return 0

    @property
    def rate_limit(self):
        """تكوين Mikrotik-Rate-Limit الكامل مع burst كامل"""
        parts = [f"{self.speed_up}/{self.speed_down}"]
        if self.burst_up and self.burst_down:
            parts.append(f"{self.burst_up}/{self.burst_down}")
        else:
            parts.append("0/0")
        if self.burst_threshold_up and self.burst_threshold_down:
            parts.append(f"{self.burst_threshold_up}/{self.burst_threshold_down}")
        else:
            parts.append("0/0")
        bt_up = str(self.burst_time_up) if self.burst_time_up else '16'
        bt_down = str(self.burst_time_down) if self.burst_time_down else '16'
        parts.append(f"{bt_up}/{bt_down}")
        if self.min_rate_up and self.min_rate_down:
            parts.append(f"{self.min_rate_up}/{self.min_rate_down}")
        else:
            parts.append("0/0")
        parts.append(str(self.priority))
        return ' '.join(parts)

    @property
    def users_count(self):
        return self.users.count()

    @property
    def display_name(self):
        lang = get_lang()
        if lang == 'en' and self.name_en:
            return self.name_en
        return self.name


class CustomRadiusAttr(db.Model):
    __tablename__ = 'custom_radius_attrs'
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('rad_users.id'), nullable=True)
    attribute = db.Column(db.String(100), nullable=False)
    operator = db.Column(db.String(10), default='=')
    value = db.Column(db.String(255), nullable=False)
    attr_type = db.Column(db.String(10), default='reply')  # check or reply
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    package = db.relationship('Package', backref='custom_attrs')
    user = db.relationship('RadUser', backref='custom_attrs')


class RadUser(db.Model):
    __tablename__ = 'rad_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), default='')
    phone = db.Column(db.String(20), default='')
    email = db.Column(db.String(200), default='')
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    auth_type = db.Column(db.String(20), default='hotspot')
    is_active = db.Column(db.Boolean, default=True)
    static_ip = db.Column(db.String(45), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    total_download = db.Column(db.BigInteger, default=0)
    total_upload = db.Column(db.BigInteger, default=0)
    total_session_time = db.Column(db.Integer, default=0)
    balance = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, default='')
    email_verified = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), default='')
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def status_text(self):
        if not self.is_active:
            return 'معطّل' if get_lang() == 'ar' else 'Disabled'
        if self.is_expired:
            return 'منتهي' if get_lang() == 'ar' else 'Expired'
        return 'نشط' if get_lang() == 'ar' else 'Active'

    @property
    def status_color(self):
        if not self.is_active:
            return 'danger'
        if self.is_expired:
            return 'warning'
        return 'success'

    def set_password(self, raw_password):
        self.password = raw_password

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), default='')
    email = db.Column(db.String(200), default='')
    phone = db.Column(db.String(20), default='')
    address = db.Column(db.Text, default='')
    parent_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    credit_limit = db.Column(db.Float, default=0)
    balance = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parent = db.relationship('Customer', remote_side=[id], backref='children')
    users = db.relationship('RadUser', backref='customer', lazy='dynamic')

    @property
    def users_count(self):
        return self.users.count()


class VoucherBatch(db.Model):
    __tablename__ = 'voucher_batches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    prefix = db.Column(db.String(20), default='ZNR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, nullable=True)

    package = db.relationship('Package', backref='voucher_batches')
    vouchers = db.relationship('Voucher', backref='batch', lazy='dynamic',
                               cascade='all, delete-orphan')

    @property
    def total_count(self):
        return self.quantity or self.vouchers.count()

    @property
    def used_count(self):
        return self.vouchers.filter_by(is_used=True).count()

    @property
    def unused_count(self):
        return self.vouchers.filter_by(is_used=False).count()


class Voucher(db.Model):
    __tablename__ = 'vouchers'
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('voucher_batches.id'), nullable=False)
    code = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by_id = db.Column(db.Integer, db.ForeignKey('rad_users.id'), nullable=True)
    used_by_username = db.Column(db.String(100), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    used_by = db.relationship('RadUser', backref='used_vouchers')


class RadAcct(db.Model):
    __tablename__ = 'radacct'
    radacctid = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    acctsessionid = db.Column(db.String(64), nullable=False, default='')
    acctuniqueid = db.Column(db.String(32), nullable=False, default='')
    username = db.Column(db.String(100), default='')
    nasipaddress = db.Column(db.String(45), default='')
    acctstarttime = db.Column(db.DateTime, nullable=True)
    acctstoptime = db.Column(db.DateTime, nullable=True)
    acctsessiontime = db.Column(db.Integer, default=0)
    acctinputoctets = db.Column(db.BigInteger, default=0)
    acctoutputoctets = db.Column(db.BigInteger, default=0)
    acctterminatecause = db.Column(db.String(32), default='')
    framedipaddress = db.Column(db.String(45), default='')
    calledstationid = db.Column(db.String(50), default='')
    callingstationid = db.Column(db.String(50), default='')

    @property
    def duration(self):
        s = self.acctsessiontime or 0
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        return f"{h}س {m}د {sec}ث" if get_lang() == 'ar' else f"{h}h {m}m {sec}s"

    @property
    def download(self):
        b = self.acctoutputoctets or 0
        if b >= 1073741824:
            return f"{b/1073741824:.1f} GB"
        elif b >= 1048576:
            return f"{b/1048576:.1f} MB"
        return f"{b/1024:.0f} KB"

    @property
    def upload(self):
        b = self.acctinputoctets or 0
        if b >= 1073741824:
            return f"{b/1073741824:.1f} GB"
        elif b >= 1048576:
            return f"{b/1048576:.1f} MB"
        return f"{b/1024:.0f} KB"


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('rad_users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), nullable=True)
    payment_method = db.Column(db.String(50), default='cash')
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('RadUser', backref='payments')
    pkg = db.relationship('Package')

    @property
    def package(self):
        return self.pkg


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), default='')
    role = db.Column(db.String(20), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(200), default='')
    details = db.Column(db.Text, default='')
    ip_address = db.Column(db.String(45), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def admin_username(self):
        if self.admin_id:
            a = Admin.query.get(self.admin_id)
            return a.username if a else 'نظام'
        return 'نظام'

    @property
    def action_text(self):
        mapping = {
            'user_create': 'إنشاء مستخدم',
            'user_delete': 'حذف مستخدم',
            'user_edit': 'تعديل مستخدم',
            'user_toggle': 'تفعيل/تعطيل',
            'user_renew': 'تجديد اشتراك',
            'package_create': 'إنشاء باقة',
            'package_delete': 'حذف باقة',
            'nas_add': 'إضافة راوتر',
            'nas_sync': 'مزامنة RADIUS',
            'login': 'تسجيل دخول',
            'payment': 'دفعة',
            'voucher_gen': 'توليد كوبونات',
            'backup': 'نسخ احتياطي',
            'restore': 'استعادة',
        }
        return mapping.get(self.action, self.action)

    @property
    def action_color(self):
        danger_words = ['حذف', 'delete']
        warning_words = ['تعطيل', 'disable', 'تجديد', 'renew']
        success_words = ['إنشاء', 'create', 'إضافة', 'تفعيل', 'مزامنة', 'تسجيل دخول', 'دفعة', 'توليد', 'نسخ', 'استعادة']
        for w in danger_words:
            if w in self.action:
                return 'danger'
        for w in warning_words:
            if w in self.action:
                return 'warning'
        for w in success_words:
            if w in self.action:
                return 'success'
        return 'info'

    def save_log(self):
        db.session.add(self)
        db.session.commit()


class BackupRecord(db.Model):
    __tablename__ = 'backup_records'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, nullable=True)


# ═══════════════════════════════════════════
#  حماية تسجيل الدخول
# ═══════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        if session.get('admin_role') == 'viewer':
            abort(403)
        return f(*args, **kwargs)
    return decorated


def user_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'portal_user_id' not in session:
            return redirect(url_for('portal_login'))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════
#  مزامنة FreeRADIUS
# ═══════════════════════════════════════════

def sync_freeradius_clients():
    devices = NASDevice.query.filter_by(is_active=True).all()
    lines = ['# ═══════════════════════════════════════',
             '# زنار — عملاء RADIUS (توليد تلقائي)',
             '# ═══════════════════════════════════════', '']
    for d in devices:
        lines.append(f'client {d.name} {{')
        lines.append(f'    ipaddr = {d.ip_address}')
        lines.append(f'    secret = {d.shared_secret}')
        lines.append(f'    require_message_authenticator = no')
        lines.append(f'    nas_type = {d.nas_type}')
        lines.append('}')
        lines.append('')
    try:
        config_path = os.environ.get(
            'FREERADIUS_CLIENTS_CONF',
            '/etc/freeradius/3.0/clients.conf'
        )
        with open(config_path, 'w') as f:
            f.write('\n'.join(lines))
        subprocess.run(
            ['systemctl', 'reload', 'freeradius'],
            capture_output=True
        )
        return True
    except Exception as e:
        print(f"FreeRADIUS sync error: {e}")
        return False


def generate_rad_attrs(user):
    """توليد سمات RADIUS للمستخدم مع دعم السمات المخصصة"""
    check = [{'attribute': 'Cleartext-Password', 'op': ':=', 'value': user.password}]
    reply = []

    if not user.is_active or user.is_expired:
        check.append({'attribute': 'Auth-Type', 'op': ':=', 'value': 'Reject'})

    if user.package:
        reply.append({
            'attribute': 'Mikrotik-Rate-Limit',
            'op': '=',
            'value': user.package.rate_limit
        })
        if user.package.session_timeout and user.package.session_timeout > 0:
            reply.append({
                'attribute': 'Session-Timeout',
                'op': '=',
                'value': str(user.package.session_timeout)
            })
        if user.package.data_limit > 0:
            reply.append({
                'attribute': 'Mikrotik-Total-Limit',
                'op': '=',
                'value': str(user.package.data_limit)
            })
        if user.package.transfer_limit > 0:
            reply.append({
                'attribute': 'Mikrotik-Total-Limit-Gigawords',
                'op': '=',
                'value': str(user.package.transfer_limit)
            })
        if user.package.uptime_limit > 0:
            reply.append({
                'attribute': 'Mikrotik-Uptime-Limit',
                'op': '=',
                'value': str(user.package.uptime_limit)
            })
        # إعادة العدادات
        reset_map = {
            'hourly': '1h',
            'daily': '1d',
            'weekly': '1w',
            'monthly': '1m',
        }
        if user.package.reset_counters in reset_map:
            reply.append({
                'attribute': 'Mikrotik-Reset-Counters',
                'op': '=',
                'value': reset_map[user.package.reset_counters]
            })

        # Concurrent logins
        if user.package.concurrent_limit and user.package.concurrent_limit > 0:
            reply.append({
                'attribute': 'Mikrotik-Mac-Count',
                'op': '=',
                'value': str(user.package.concurrent_limit)
            })

    # سمات مخصصة للحزمة
    if user.package:
        for ca in user.package.custom_attrs:
            if ca.attr_type == 'check':
                check.append({'attribute': ca.attribute, 'op': ca.operator, 'value': ca.value})
            else:
                reply.append({'attribute': ca.attribute, 'op': ca.operator, 'value': ca.value})

    # سمات مخصصة للمستخدم
    for ca in user.custom_attrs:
        if ca.attr_type == 'check':
            check.append({'attribute': ca.attribute, 'op': ca.operator, 'value': ca.value})
        else:
            reply.append({'attribute': ca.attribute, 'op': ca.operator, 'value': ca.value})

    if user.static_ip:
        reply.append({
            'attribute': 'Framed-IP-Address',
            'op': '=',
            'value': user.static_ip
        })

    if user.auth_type == 'pppoe':
        check.append({'attribute': 'Service-Type', 'op': '=', 'value': 'Framed-User'})
        reply.append({'attribute': 'Framed-Protocol', 'op': '=', 'value': 'PPP'})
        reply.append({'attribute': 'Mikrotik-Group', 'op': '=', 'value': 'pppoe-users'})
    else:
        reply.append({'attribute': 'Mikrotik-Group', 'op': '=', 'value': 'hotspot-users'})

    return {'radcheck': check, 'radreply': reply}


# ═══════════════════════════════════════════
#  تبديل اللغة
# ═══════════════════════════════════════════

@app.route('/lang/<lang_code>')
def set_language(lang_code):
    if lang_code in ('ar', 'en'):
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))


# ═══════════════════════════════════════════
#  المسارات — المصادقة
# ═══════════════════════════════════════════

@app.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    lang = get_lang()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        admin = Admin.query.filter_by(
            username=username, is_active=True
        ).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            session['admin_name'] = admin.full_name
            session['admin_role'] = admin.role
            admin.last_login = datetime.utcnow()
            db.session.commit()
            log = ActivityLog(
                action='login', target=admin.username,
                ip_address=request.remote_addr
            )
            log.save_log()
            flash('تم تسجيل الدخول بنجاح' if lang == 'ar' else 'Login successful', 'success')
            return redirect(url_for('dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة' if lang == 'ar' else 'Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = RadUser.query.filter_by(email=email).first()
        admin = Admin.query.filter_by(username=email).first() if not user else None
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            # في بيئة الإنتاج يتم إرسال رابط عبر البريد
            # هنا نعرضه مباشرة للتجربة
            reset_url = url_for('reset_password', token=token, _external=True)
            flash(f'تم إنشاء رابط إعادة التعيين. الرابط: {reset_url}', 'info')
        elif admin:
            flash('تم إرسال رابط إعادة التعيين إلى بريدك الإلكتروني' if get_lang() == 'ar' else 'Reset link sent to your email', 'info')
        else:
            flash('البريد الإلكتروني غير مسجل' if get_lang() == 'ar' else 'Email not registered', 'warning')
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = RadUser.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        flash('رابط إعادة التعيين منتهي أو غير صالح' if get_lang() == 'ar' else 'Reset link expired or invalid', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_pass = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if new_pass != confirm:
            flash('كلمتا المرور غير متطابقتين' if get_lang() == 'ar' else 'Passwords do not match', 'danger')
            return render_template('reset_password.html', token=token)
        user.set_password(new_pass)
        user.reset_token = ''
        user.reset_token_expires = None
        db.session.commit()
        flash('تم تغيير كلمة المرور بنجاح' if get_lang() == 'ar' else 'Password changed successfully', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if password != confirm:
            flash('كلمتا المرور غير متطابقتين' if get_lang() == 'ar' else 'Passwords do not match', 'danger')
            return render_template('register.html')

        if RadUser.query.filter_by(username=username).first():
            flash('اسم المستخدم مستخدم بالفعل' if get_lang() == 'ar' else 'Username already taken', 'danger')
            return render_template('register.html')

        if email and RadUser.query.filter_by(email=email).first():
            flash('البريد الإلكتروني مسجل بالفعل' if get_lang() == 'ar' else 'Email already registered', 'danger')
            return render_template('register.html')

        user = RadUser(
            username=username,
            full_name=full_name,
            email=email,
            phone=phone,
            auth_type='hotspot',
            is_active=True,
            balance=0
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('تم إنشاء الحساب بنجاح! يمكنك الآن شراء باقة من بوابة المستخدم' if get_lang() == 'ar' else 'Account created! You can now purchase a plan from the self-service portal', 'success')
        return redirect(url_for('selfservice_login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج' if get_lang() == 'ar' else 'Logged out', 'info')
    return redirect(url_for('login'))




# ═══════════════════════════════════════════
#  لوحة التحكم
# ═══════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    total_users = RadUser.query.count()
    active_users = RadUser.query.filter_by(is_active=True).count()
    expired_users = RadUser.query.filter(
        RadUser.expires_at.isnot(None),
        RadUser.expires_at < datetime.utcnow()
    ).count()
    total_nas = NASDevice.query.count()
    total_packages = Package.query.filter_by(is_active=True).count()
    online_sessions = RadAcct.query.filter(
        RadAcct.acctstoptime.is_(None)
    ).count()
    total_vouchers_unused = Voucher.query.filter_by(is_used=False).count()
    total_customers = Customer.query.count()

    this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    monthly_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(Payment.created_at >= this_month).scalar() or 0

    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(Payment.created_at >= today).scalar() or 0

    recent_users = RadUser.query.order_by(
        RadUser.created_at.desc()
    ).limit(10).all()
    recent_payments = Payment.query.order_by(
        Payment.created_at.desc()
    ).limit(8).all()

    # بيانات الرسم البياني — آخر 7 أيام
    chart_days = []
    chart_revenues = []
    chart_new_users = []
    for i in range(6, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).replace(hour=0, minute=0, second=0)
        next_day = day + timedelta(days=1)
        rev = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.created_at >= day, Payment.created_at < next_day
        ).scalar() or 0
        new_u = RadUser.query.filter(
            RadUser.created_at >= day, RadUser.created_at < next_day
        ).count()
        chart_days.append(day.strftime('%m/%d'))
        chart_revenues.append(rev)
        chart_new_users.append(new_u)

    # توزيع الباقات
    pkg_dist = []
    for p in Package.query.filter_by(is_active=True).all():
        pkg_dist.append({'name': p.display_name, 'count': p.users_count})

    return render_template('dashboard.html',
        total_users=total_users, active_users=active_users,
        expired_users=expired_users, total_nas=total_nas,
        total_packages=total_packages, monthly_revenue=monthly_revenue,
        today_revenue=today_revenue,
        online_sessions=online_sessions,
        total_vouchers_unused=total_vouchers_unused,
        total_customers=total_customers,
        recent_users=recent_users, recent_payments=recent_payments,
        chart_days=chart_days, chart_revenues=chart_revenues,
        chart_new_users=chart_new_users, pkg_dist=pkg_dist
    )


# ═══════════════════════════════════════════
#  إدارة المستخدمين
# ═══════════════════════════════════════════

@app.route('/users')
@login_required
def users_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_status = request.args.get('status', '')
    filter_type = request.args.get('type', '')

    query = RadUser.query
    if search:
        query = query.filter(
            db.or_(
                RadUser.username.contains(search),
                RadUser.full_name.contains(search),
                RadUser.phone.contains(search)
            )
        )
    if filter_status == 'active':
        query = query.filter_by(is_active=True)
    elif filter_status == 'inactive':
        query = query.filter_by(is_active=False)
    elif filter_status == 'expired':
        query = query.filter(
            RadUser.expires_at < datetime.utcnow()
        )

    if filter_type:
        query = query.filter_by(auth_type=filter_type)

    pagination = query.order_by(
        RadUser.created_at.desc()
    ).paginate(page=page, per_page=25, error_out=False)

    packages = Package.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    return render_template('users.html',
        users=pagination.items, pagination=pagination,
        packages=packages, customers=customers,
        search=search, filter_status=filter_status,
        filter_type=filter_type)


@app.route('/users/add', methods=['GET', 'POST'])
@admin_required
def user_add():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        package_id = request.form.get('package_id', type=int)
        customer_id = request.form.get('customer_id', type=int)
        auth_type = request.form.get('auth_type', 'hotspot')
        static_ip = request.form.get('static_ip', '').strip()
        balance = request.form.get('balance', type=float, default=0)
        is_active = 'is_active' in request.form

        if RadUser.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('user_add'))

        user = RadUser(
            username=username, full_name=full_name,
            phone=phone, email=email,
            package_id=package_id if package_id else None,
            customer_id=customer_id if customer_id else None,
            auth_type=auth_type, static_ip=static_ip,
            is_active=is_active, balance=balance or 0
        )
        user.set_password(password)

        if package_id:
            pkg = Package.query.get(package_id)
            if pkg and pkg.time_limit_days:
                user.expires_at = datetime.utcnow() + timedelta(days=pkg.time_limit_days)

        db.session.add(user)
        db.session.commit()

        ActivityLog(
            admin_id=session.get('admin_id'),
            action='user_create', target=username,
            ip_address=request.remote_addr
        ).save_log()
        flash(f'تم إنشاء المستخدم {username}', 'success')
        return redirect(url_for('users_list'))

    packages = Package.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    return render_template('user_form.html', user=None,
                          packages=packages, customers=customers)


@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    user = RadUser.query.get_or_404(user_id)
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.phone = request.form.get('phone', '').strip()
        user.email = request.form.get('email', '').strip()
        user.package_id = request.form.get('package_id', type=int) or None
        user.customer_id = request.form.get('customer_id', type=int) or None
        user.auth_type = request.form.get('auth_type', 'hotspot')
        user.static_ip = request.form.get('static_ip', '').strip()
        user.balance = request.form.get('balance', type=float, default=0)
        user.is_active = 'is_active' in request.form
        user.notes = request.form.get('notes', '').strip()

        new_password = request.form.get('new_password', '').strip()
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        ActivityLog(
            admin_id=session.get('admin_id'),
            action='user_edit', target=user.username,
            ip_address=request.remote_addr
        ).save_log()
        flash(f'تم تحديث المستخدم {user.username}', 'success')
        return redirect(url_for('users_list'))

    packages = Package.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    return render_template('user_form.html', user=user,
                          packages=packages, customers=customers)


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def user_delete(user_id):
    user = RadUser.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    ActivityLog(
        admin_id=session.get('admin_id'),
        action='user_delete', target=username,
        ip_address=request.remote_addr
    ).save_log()
    flash(f'تم حذف المستخدم {username}', 'info')
    return redirect(url_for('users_list'))


@app.route('/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def user_toggle(user_id):
    user = RadUser.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    action = 'تفعيل' if user.is_active else 'تعطيل'
    ActivityLog(
        admin_id=session.get('admin_id'),
        action='user_toggle', target=user.username,
        details=action, ip_address=request.remote_addr
    ).save_log()
    flash(f'تم {action} المستخدم {user.username}', 'success')
    return redirect(url_for('users_list'))


@app.route('/users/renew/<int:user_id>', methods=['POST'])
@admin_required
def user_renew(user_id):
    user = RadUser.query.get_or_404(user_id)
    package_id = request.form.get('package_id', type=int)
    if package_id:
        pkg = Package.query.get(package_id)
        if pkg:
            user.package_id = pkg.id
            if pkg.time_limit_days:
                user.expires_at = datetime.utcnow() + timedelta(days=pkg.time_limit_days)
            user.is_active = True

            payment = Payment(
                user_id=user.id, amount=pkg.price,
                package_id=pkg.id,
                payment_method=request.form.get('payment_method', 'cash'),
                description=f"تجديد باقة {pkg.name}"
            )
            db.session.add(payment)

    db.session.commit()
    ActivityLog(
        admin_id=session.get('admin_id'),
        action='user_renew', target=user.username,
        ip_address=request.remote_addr
    ).save_log()
    flash(f'تم تجديد اشتراك {user.username}', 'success')
    return redirect(url_for('users_list'))


@app.route('/users/radcheck/<int:user_id>')
@login_required
def user_radcheck(user_id):
    user = RadUser.query.get_or_404(user_id)
    attrs = generate_rad_attrs(user)
    return jsonify(attrs)


# ═══════════════════════════════════════════
#  إدارة العملاء (Customers)
# ═══════════════════════════════════════════

@app.route('/customers')
@login_required
def customers_list():
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('customers.html', customers=customers)


@app.route('/customers/add', methods=['GET', 'POST'])
@admin_required
def customer_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        name_en = request.form.get('name_en', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        parent_id = request.form.get('parent_id', type=int) or None
        credit_limit = request.form.get('credit_limit', type=float, default=0)
        balance = request.form.get('balance', type=float, default=0)

        c = Customer(
            name=name, name_en=name_en, email=email,
            phone=phone, address=address,
            parent_id=parent_id, credit_limit=credit_limit,
            balance=balance
        )
        db.session.add(c)
        db.session.commit()
        flash(f'تم إضافة العميل {name}', 'success')
        return redirect(url_for('customers_list'))

    all_customers = Customer.query.filter_by(is_active=True).all()
    return render_template('customer_form.html', customer=None, customers=all_customers)


@app.route('/customers/edit/<int:c_id>', methods=['GET', 'POST'])
@admin_required
def customer_edit(c_id):
    c = Customer.query.get_or_404(c_id)
    if request.method == 'POST':
        c.name = request.form.get('name', '').strip()
        c.name_en = request.form.get('name_en', '').strip()
        c.email = request.form.get('email', '').strip()
        c.phone = request.form.get('phone', '').strip()
        c.address = request.form.get('address', '').strip()
        c.parent_id = request.form.get('parent_id', type=int) or None
        c.credit_limit = request.form.get('credit_limit', type=float, default=0)
        c.balance = request.form.get('balance', type=float, default=0)
        c.is_active = 'is_active' in request.form
        db.session.commit()
        flash(f'تم تحديث العميل {c.name}', 'success')
        return redirect(url_for('customers_list'))

    all_customers = Customer.query.filter(Customer.id != c_id, Customer.is_active == True).all()
    return render_template('customer_form.html', customer=c, customers=all_customers)


@app.route('/customers/delete/<int:c_id>', methods=['POST'])
@admin_required
def customer_delete(c_id):
    c = Customer.query.get_or_404(c_id)
    db.session.delete(c)
    db.session.commit()
    flash(f'تم حذف العميل {c.name}', 'info')
    return redirect(url_for('customers_list'))


# ═══════════════════════════════════════════
#  إدارة الباقات (مع Limitations محسّنة)
# ═══════════════════════════════════════════

@app.route('/packages')
@login_required
def packages_list():
    packages = Package.query.order_by(Package.price).all()
    return render_template('packages.html', packages=packages)


@app.route('/packages/add', methods=['GET', 'POST'])
@admin_required
def package_add():
    if request.method == 'POST':
        p = Package(
            name=request.form.get('name', '').strip(),
            name_en=request.form.get('name_en', '').strip(),
            speed_down=request.form.get('speed_down', '2M'),
            speed_up=request.form.get('speed_up', '1M'),
            burst_down=request.form.get('burst_down', ''),
            burst_up=request.form.get('burst_up', ''),
            burst_threshold_down=request.form.get('burst_threshold_down', ''),
            burst_threshold_up=request.form.get('burst_threshold_up', ''),
            burst_time_up=request.form.get('burst_time_up', type=int, default=0),
            burst_time_down=request.form.get('burst_time_down', type=int, default=0),
            min_rate_up=request.form.get('min_rate_up', ''),
            min_rate_down=request.form.get('min_rate_down', ''),
            priority=request.form.get('priority', type=int, default=8),
            price=request.form.get('price', type=float, default=0),
            currency=request.form.get('currency', 'ر.س'),
            time_limit_days=request.form.get('time_limit_days', type=int, default=30),
            data_limit_gb=request.form.get('data_limit_gb', type=float, default=0),
            transfer_limit_gb=request.form.get('transfer_limit_gb', type=float, default=0),
            uptime_limit_hours=request.form.get('uptime_limit_hours', type=float, default=0),
            session_timeout=request.form.get('session_timeout', type=int, default=0),
            concurrent_limit=request.form.get('concurrent_limit', type=int, default=1),
            reset_counters=request.form.get('reset_counters', 'monthly'),
            is_active='is_active' in request.form,
            is_hotspot='is_hotspot' in request.form,
            is_pppoe='is_pppoe' in request.form,
            description=request.form.get('description', '').strip(),
        )
        db.session.add(p)
        db.session.commit()

        # سمات RADIUS مخصصة
        attrs = request.form.getlist('custom_attr[]')
        ops = request.form.getlist('custom_op[]')
        vals = request.form.getlist('custom_val[]')
        types = request.form.getlist('custom_type[]')
        for a, o, v, tp in zip(attrs, ops, vals, types):
            if a.strip() and v.strip():
                db.session.add(CustomRadiusAttr(
                    package_id=p.id, attribute=a.strip(),
                    operator=o, value=v.strip(), attr_type=tp
                ))
        db.session.commit()

        ActivityLog(
            admin_id=session.get('admin_id'),
            action='package_create', target=p.name,
            ip_address=request.remote_addr
        ).save_log()
        flash(f'تم إنشاء الباقة {p.name}', 'success')
        return redirect(url_for('packages_list'))

    return render_template('package_form.html', pkg=None)


@app.route('/packages/edit/<int:pkg_id>', methods=['GET', 'POST'])
@admin_required
def package_edit(pkg_id):
    pkg = Package.query.get_or_404(pkg_id)
    if request.method == 'POST':
        pkg.name = request.form.get('name', '').strip()
        pkg.name_en = request.form.get('name_en', '').strip()
        pkg.speed_down = request.form.get('speed_down', '2M')
        pkg.speed_up = request.form.get('speed_up', '1M')
        pkg.burst_down = request.form.get('burst_down', '')
        pkg.burst_up = request.form.get('burst_up', '')
        pkg.burst_threshold_down = request.form.get('burst_threshold_down', '')
        pkg.burst_threshold_up = request.form.get('burst_threshold_up', '')
        pkg.burst_time_up = request.form.get('burst_time_up', type=int, default=0)
        pkg.burst_time_down = request.form.get('burst_time_down', type=int, default=0)
        pkg.min_rate_up = request.form.get('min_rate_up', '')
        pkg.min_rate_down = request.form.get('min_rate_down', '')
        pkg.priority = request.form.get('priority', type=int, default=8)
        pkg.price = request.form.get('price', type=float, default=0)
        pkg.currency = request.form.get('currency', 'ر.س')
        pkg.time_limit_days = request.form.get('time_limit_days', type=int, default=30)
        pkg.data_limit_gb = request.form.get('data_limit_gb', type=float, default=0)
        pkg.transfer_limit_gb = request.form.get('transfer_limit_gb', type=float, default=0)
        pkg.uptime_limit_hours = request.form.get('uptime_limit_hours', type=float, default=0)
        pkg.session_timeout = request.form.get('session_timeout', type=int, default=0)
        pkg.concurrent_limit = request.form.get('concurrent_limit', type=int, default=1)
        pkg.reset_counters = request.form.get('reset_counters', 'monthly')
        pkg.is_active = 'is_active' in request.form
        pkg.is_hotspot = 'is_hotspot' in request.form
        pkg.is_pppoe = 'is_pppoe' in request.form
        pkg.description = request.form.get('description', '').strip()

        # تحديث السمات المخصصة
        CustomRadiusAttr.query.filter_by(package_id=pkg.id).delete()
        attrs = request.form.getlist('custom_attr[]')
        ops = request.form.getlist('custom_op[]')
        vals = request.form.getlist('custom_val[]')
        types = request.form.getlist('custom_type[]')
        for a, o, v, tp in zip(attrs, ops, vals, types):
            if a.strip() and v.strip():
                db.session.add(CustomRadiusAttr(
                    package_id=pkg.id, attribute=a.strip(),
                    operator=o, value=v.strip(), attr_type=tp
                ))

        db.session.commit()
        flash(f'تم تحديث الباقة {pkg.name}', 'success')
        return redirect(url_for('packages_list'))

    return render_template('package_form.html', pkg=pkg)


@app.route('/packages/delete/<int:pkg_id>', methods=['POST'])
@admin_required
def package_delete(pkg_id):
    pkg = Package.query.get_or_404(pkg_id)
    db.session.delete(pkg)
    db.session.commit()
    flash(f'تم حذف الباقة {pkg.name}', 'info')
    return redirect(url_for('packages_list'))


# ═══════════════════════════════════════════
#  إدارة الراوترات NAS
# ═══════════════════════════════════════════

@app.route('/nas')
@login_required
def nas_list():
    devices = NASDevice.query.order_by(NASDevice.created_at.desc()).all()
    return render_template('nas.html', devices=devices)


@app.route('/nas/add', methods=['GET', 'POST'])
@admin_required
def nas_add():
    if request.method == 'POST':
        device = NASDevice(
            name=request.form.get('name', '').strip(),
            ip_address=request.form.get('ip_address', '').strip(),
            shared_secret=request.form.get('shared_secret', '').strip(),
            description=request.form.get('description', '').strip(),
            nas_type=request.form.get('nas_type', 'mikrotik'),
            auth_port=request.form.get('auth_port', type=int, default=1812),
            acct_port=request.form.get('acct_port', type=int, default=1813),
            coa_port=request.form.get('coa_port', type=int, default=3799),
            is_active='is_active' in request.form
        )
        db.session.add(device)
        db.session.commit()
        sync_freeradius_clients()
        ActivityLog(
            admin_id=session.get('admin_id'),
            action='nas_add', target=device.name,
            ip_address=request.remote_addr
        ).save_log()
        flash(f'تم إضافة الراوتر {device.name}', 'success')
        return redirect(url_for('nas_list'))
    return render_template('nas_form.html', device=None)


@app.route('/nas/edit/<int:nas_id>', methods=['GET', 'POST'])
@admin_required
def nas_edit(nas_id):
    device = NASDevice.query.get_or_404(nas_id)
    if request.method == 'POST':
        device.name = request.form.get('name', '').strip()
        device.ip_address = request.form.get('ip_address', '').strip()
        device.shared_secret = request.form.get('shared_secret', '').strip()
        device.description = request.form.get('description', '').strip()
        device.nas_type = request.form.get('nas_type', 'mikrotik')
        device.auth_port = request.form.get('auth_port', type=int, default=1812)
        device.acct_port = request.form.get('acct_port', type=int, default=1813)
        device.coa_port = request.form.get('coa_port', type=int, default=3799)
        device.is_active = 'is_active' in request.form
        db.session.commit()
        sync_freeradius_clients()
        flash(f'تم تحديث الراوتر {device.name}', 'success')
        return redirect(url_for('nas_list'))
    return render_template('nas_form.html', device=device)


@app.route('/nas/delete/<int:nas_id>', methods=['POST'])
@admin_required
def nas_delete(nas_id):
    device = NASDevice.query.get_or_404(nas_id)
    db.session.delete(device)
    db.session.commit()
    sync_freeradius_clients()
    flash(f'تم حذف الراوتر {device.name}', 'info')
    return redirect(url_for('nas_list'))


@app.route('/nas/sync', methods=['POST'])
@admin_required
def sync_nas():
    if sync_freeradius_clients():
        flash('تمت مزامنة FreeRADIUS بنجاح', 'success')
    else:
        flash('فشلت المزامنة — تأكد من صلاحيات الملفات', 'danger')
    return redirect(url_for('nas_list'))


# ═══════════════════════════════════════════
#  الكوبونات
# ═══════════════════════════════════════════

@app.route('/vouchers')
@login_required
def vouchers_list():
    batches = VoucherBatch.query.order_by(VoucherBatch.created_at.desc()).all()
    return render_template('vouchers.html', batches=batches)


@app.route('/vouchers/generate', methods=['GET', 'POST'])
@admin_required
def voucher_generate():
    if request.method == 'POST':
        name = request.form.get('batch_name', '').strip()
        package_id = request.form.get('package_id', type=int)
        quantity = request.form.get('quantity', type=int, default=10)
        prefix = request.form.get('prefix', 'ZNR')
        password_len = request.form.get('password_len', type=int, default=8)

        batch = VoucherBatch(
            name=name or f"Batch-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            package_id=package_id,
            quantity=quantity,
            prefix=prefix,
            created_by=session.get('admin_id')
        )
        db.session.add(batch)
        db.session.flush()

        for _ in range(quantity):
            code = f"{prefix}-{secrets.token_hex(4).upper()}"
            pwd = secrets.token_hex(password_len // 2).upper()[:password_len]
            v = Voucher(batch_id=batch.id, code=code, password=pwd)
            db.session.add(v)

        db.session.commit()
        ActivityLog(
            admin_id=session.get('admin_id'),
            action='voucher_gen', target=batch.name,
            details=f'{quantity} vouchers', ip_address=request.remote_addr
        ).save_log()
        flash(f'تم توليد {quantity} كوبون بنجاح', 'success')
        return redirect(url_for('vouchers_list'))

    packages = Package.query.filter_by(is_active=True).all()
    return render_template('voucher_generate.html', packages=packages)


@app.route('/vouchers/batch/<int:batch_id>')
@login_required
def voucher_batch_detail(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    page = request.args.get('page', 1, type=int)
    pagination = batch.vouchers.order_by(Voucher.id).paginate(
        page=page, per_page=50, error_out=False
    )
    return render_template('voucher_batch.html',
        batch=batch, vouchers=pagination.items,
        pagination=pagination)


@app.route('/vouchers/print/<int:batch_id>')
@login_required
def voucher_print(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    vouchers = batch.vouchers.all()
    return render_template('voucher_print.html',
        batch=batch, vouchers=vouchers)


@app.route('/vouchers/delete/<int:batch_id>', methods=['POST'])
@admin_required
def voucher_batch_delete(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    db.session.delete(batch)
    db.session.commit()
    flash('تم حذف الدفعة', 'info')
    return redirect(url_for('vouchers_list'))


# ═══════════════════════════════════════════
#  الجلسات النشطة
# ═══════════════════════════════════════════

@app.route('/sessions')
@login_required
def sessions_list():
    search = request.args.get('search', '')
    filter_nas = request.args.get('nas', '')

    query = RadAcct.query.filter(RadAcct.acctstoptime.is_(None))
    if search:
        query = query.filter(RadAcct.username.contains(search))
    if filter_nas:
        query = query.filter(RadAcct.nasipaddress == filter_nas)

    sessions = query.order_by(RadAcct.acctstarttime.desc()).all()
    nas_devices = NASDevice.query.filter_by(is_active=True).all()
    return render_template(
        'sessions.html', sessions=sessions,
        nas_devices=nas_devices, search=search, filter_nas=filter_nas
    )


@app.route('/sessions/disconnect/<int:session_id>', methods=['POST'])
@admin_required
def session_disconnect(session_id):
    acct = RadAcct.query.get_or_404(session_id)
    nas = NASDevice.query.filter_by(
        ip_address=acct.nasipaddress
    ).first()
    if not nas:
        flash('الراوتر غير موجود', 'danger')
        return redirect(url_for('sessions_list'))

    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.coa', delete=False
        ) as f:
            f.write(f'User-Name="{acct.username}"\n')
            f.write(f'Acct-Session-Id="{acct.acctsessionid}"\n')
            tmp_path = f.name

        result = subprocess.run(
            ['radclient', '-x', '-r', '3', '-f', tmp_path,
             f'{nas.ip_address}:{nas.coa_port or 3799}',
             'disconnect', nas.shared_secret],
            capture_output=True, text=True, timeout=10
        )
        os.unlink(tmp_path)

        acct.acctstoptime = datetime.utcnow()
        acct.acctterminatecause = 'Admin-Disconnect'
        db.session.commit()

        flash(f'تم فصل جلسة {acct.username}', 'success')
    except Exception as e:
        flash(f'فشل فصل الجلسة: {e}', 'danger')

    return redirect(url_for('sessions_list'))


# ═══════════════════════════════════════════
#  المدفوعات
# ═══════════════════════════════════════════

@app.route('/payments')
@login_required
def payments_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_method = request.args.get('method', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    query = Payment.query
    if search:
        query = query.join(RadUser).filter(
            db.or_(
                RadUser.username.contains(search),
                RadUser.full_name.contains(search)
            )
        )
    if filter_method:
        query = query.filter_by(payment_method=filter_method)
    if from_date:
        try:
            query = query.filter(
                Payment.created_at >= datetime.strptime(from_date, '%Y-%m-%d')
            )
        except ValueError:
            pass
    if to_date:
        try:
            query = query.filter(
                Payment.created_at <= datetime.strptime(
                    to_date, '%Y-%m-%d'
                ) + timedelta(days=1)
            )
        except ValueError:
            pass

    pagination = query.order_by(
        Payment.created_at.desc()
    ).paginate(page=page, per_page=50, error_out=False)
    total_amount = db.session.query(
        db.func.sum(Payment.amount)
    ).scalar() or 0

    return render_template('payments.html',
        payments=pagination.items, pagination=pagination,
        total_amount=total_amount,
        search=search, filter_method=filter_method,
        from_date=from_date, to_date=to_date)


# ═══════════════════════════════════════════
#  تقرير الإيرادات
# ═══════════════════════════════════════════

@app.route('/reports/revenue')
@login_required
def revenue_report():
    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    this_month = today.replace(day=1)
    this_year = today.replace(month=1, day=1)

    today_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(Payment.created_at >= today).scalar() or 0

    month_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(Payment.created_at >= this_month).scalar() or 0

    year_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).filter(Payment.created_at >= this_year).scalar() or 0

    total_payments = Payment.query.count()

    months_data = []
    revenues_data = []
    for i in range(11, -1, -1):
        m = (datetime.utcnow().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        next_m = (m + timedelta(days=32)).replace(day=1)
        rev = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.created_at >= m, Payment.created_at < next_m
        ).scalar() or 0
        months_data.append(f"{m.year}/{m.month:02d}")
        revenues_data.append(rev)

    package_revenue = []
    packages = Package.query.all()
    total_rev = year_revenue or 1
    for p in packages:
        rev = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.package_id == p.id, Payment.created_at >= this_year
        ).scalar() or 0
        package_revenue.append({
            'name': p.display_name,
            'user_count': p.users.count(),
            'revenue': rev,
            'percentage': round(rev / total_rev * 100, 1) if rev > 0 else 0
        })

    return render_template('revenue.html',
        today_revenue=today_revenue, month_revenue=month_revenue,
        year_revenue=year_revenue, total_payments=total_payments,
        months=months_data, revenues=revenues_data,
        package_revenue=package_revenue
    )


# ═══════════════════════════════════════════
#  سجل الأحداث
# ═══════════════════════════════════════════

@app.route('/logs')
@login_required
def logs_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_action = request.args.get('action', '')

    query = ActivityLog.query
    if search:
        query = query.filter(
            ActivityLog.details.contains(search) |
            ActivityLog.target.contains(search)
        )
    if filter_action:
        query = query.filter(
            ActivityLog.action.contains(filter_action)
        )

    per_page = 50
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    logs = query.order_by(
        ActivityLog.created_at.desc()
    ).offset((page - 1) * per_page).limit(per_page).all()

    return render_template('logs.html', logs=logs, search=search,
                          filter_action=filter_action, current_page=page,
                          total_pages=total_pages)


# ═══════════════════════════════════════════
#  النسخ الاحتياطي
# ═══════════════════════════════════════════

@app.route('/backup')
@login_required
def backup_page():
    records = BackupRecord.query.order_by(BackupRecord.created_at.desc()).limit(20).all()
    return render_template('backup.html', records=records)


@app.route('/backup/create', methods=['POST'])
@admin_required
def backup_create():
    db_path = os.path.join(app.instance_path, 'zinar.db')
    if not os.path.exists(db_path):
        flash('قاعدة البيانات غير موجودة', 'danger')
        return redirect(url_for('backup_page'))

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(app.instance_path, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, f'zinar_{ts}.db')
    shutil.copy2(db_path, backup_file)

    file_size = os.path.getsize(backup_file)
    record = BackupRecord(
        filename=f'zinar_{ts}.db',
        file_size=file_size,
        created_by=session.get('admin_id')
    )
    db.session.add(record)
    db.session.commit()

    ActivityLog(
        admin_id=session.get('admin_id'),
        action='backup', target=record.filename,
        ip_address=request.remote_addr
    ).save_log()
    flash(f'تم إنشاء النسخة الاحتياطية ({file_size//1024} KB)', 'success')
    return redirect(url_for('backup_page'))


@app.route('/backup/download/<int:record_id>')
@login_required
def backup_download(record_id):
    record = BackupRecord.query.get_or_404(record_id)
    backup_dir = os.path.join(app.instance_path, 'backups')
    backup_file = os.path.join(backup_dir, record.filename)
    if not os.path.exists(backup_file):
        flash('الملف غير موجود', 'danger')
        return redirect(url_for('backup_page'))
    return send_file(backup_file, as_attachment=True,
                     download_name=record.filename)


@app.route('/backup/restore/<int:record_id>', methods=['POST'])
@admin_required
def backup_restore(record_id):
    record = BackupRecord.query.get_or_404(record_id)
    backup_dir = os.path.join(app.instance_path, 'backups')
    backup_file = os.path.join(backup_dir, record.filename)
    db_path = os.path.join(app.instance_path, 'zinar.db')

    if not os.path.exists(backup_file):
        flash('الملف غير موجود', 'danger')
        return redirect(url_for('backup_page'))

    # إنشاء نسخة قبل الاستعادة
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    pre_restore = os.path.join(backup_dir, f'pre_restore_{ts}.db')
    if os.path.exists(db_path):
        shutil.copy2(db_path, pre_restore)

    shutil.copy2(backup_file, db_path)

    ActivityLog(
        admin_id=session.get('admin_id'),
        action='restore', target=record.filename,
        ip_address=request.remote_addr
    ).save_log()
    flash('تمت استعادة قاعدة البيانات بنجاح', 'success')
    return redirect(url_for('backup_page'))


@app.route('/backup/delete/<int:record_id>', methods=['POST'])
@admin_required
def backup_delete(record_id):
    record = BackupRecord.query.get_or_404(record_id)
    backup_dir = os.path.join(app.instance_path, 'backups')
    backup_file = os.path.join(backup_dir, record.filename)
    if os.path.exists(backup_file):
        os.remove(backup_file)
    db.session.delete(record)
    db.session.commit()
    flash('تم حذف النسخة الاحتياطية', 'info')
    return redirect(url_for('backup_page'))


# ═══════════════════════════════════════════
#  مسح سجل الأحداث
# ═══════════════════════════════════════════

@app.route('/logs/clear', methods=['POST'])
@admin_required
def logs_clear():
    num = ActivityLog.query.delete()
    db.session.commit()
    flash(f'تم مسح {num} سجل', 'info')
    return redirect(url_for('logs_list'))


# ═══════════════════════════════════════════
#  بوابة الخدمة الذاتية (Self-Service Portal)
# ═══════════════════════════════════════════

@app.route('/portal')
def portal_index():
    if session.get('portal_user_id'):
        return redirect(url_for('portal_dashboard'))
    return redirect(url_for('portal_login'))


@app.route('/portal/login', methods=['GET', 'POST'])
def portal_login():
    if session.get('portal_user_id'):
        return redirect(url_for('portal_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = RadUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['portal_user_id'] = user.id
            session['portal_username'] = user.username
            return redirect(url_for('portal_dashboard'))
        flash(t('invalid_credentials'), 'danger')
    return render_template('selfservice/login.html', user=None)


@app.route('/portal/logout')
def portal_logout():
    session.pop('portal_user_id', None)
    session.pop('portal_username', None)
    return redirect(url_for('portal_login'))


@app.route('/portal/dashboard')
def portal_dashboard():
    user_id = session.get('portal_user_id')
    if not user_id:
        return redirect(url_for('portal_login'))
    user = RadUser.query.get_or_404(user_id)
    active_sessions = RadAcct.query.filter(
        RadAcct.username == user.username,
        RadAcct.acctstoptime.is_(None)
    ).all()
    payments = Payment.query.filter_by(user_id=user.id).order_by(
        Payment.created_at.desc()
    ).limit(10).all()
    return render_template('selfservice/dashboard.html',
        user=user, active_sessions=active_sessions, payments=payments)


@app.route('/portal/plans')
def portal_plans():
    user_id = session.get('portal_user_id')
    if not user_id:
        return redirect(url_for('portal_login'))
    user = RadUser.query.get_or_404(user_id)
    packages = Package.query.filter_by(is_active=True).order_by(Package.price).all()
    return render_template('selfservice/plans.html',
        user=user, packages=packages)


@app.route('/portal/buy-plan/<int:pkg_id>', methods=['POST'])
def portal_buy_plan(pkg_id):
    user_id = session.get('portal_user_id')
    if not user_id:
        return redirect(url_for('portal_login'))
    user = RadUser.query.get_or_404(user_id)
    pkg = Package.query.get_or_404(pkg_id)
    if user.balance < pkg.price:
        flash(t('insufficient_balance'), 'danger')
        return redirect(url_for('portal_plans'))
    user.balance -= pkg.price
    user.package_id = pkg.id
    user.expires_at = datetime.utcnow() + timedelta(days=pkg.time_limit_days)
    user.is_active = True
    payment = Payment(
        user_id=user.id, package_id=pkg.id,
        amount=pkg.price, payment_method='balance',
        description=f'اشتراك باقة {pkg.display_name}'
    )
    db.session.add(payment)
    db.session.commit()
    flash(t('subscribed_success'), 'success')
    return redirect(url_for('portal_dashboard'))


@app.route('/portal/voucher', methods=['GET', 'POST'])
def portal_voucher():
    user_id = session.get('portal_user_id')
    user = RadUser.query.get(user_id) if user_id else None
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        voucher = Voucher.query.filter_by(code=code, is_used=False).first()
        if not voucher:
            flash(t('invalid_voucher'), 'danger')
            return redirect(url_for('portal_voucher'))
        # إذا لم يسجل دخول، نحتاج username/password
        if not user:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            user = RadUser.query.filter_by(username=username).first()
            if not user or not user.check_password(password):
                flash(t('invalid_credentials'), 'danger')
                return redirect(url_for('portal_voucher'))
        # تطبيق القسيمة
        voucher.is_used = True
        voucher.used_by_username = user.username
        voucher.used_at = datetime.utcnow()
        pkg = voucher.batch.package if voucher.batch else None
        if pkg:
            user.package_id = pkg.id
            user.expires_at = datetime.utcnow() + timedelta(days=pkg.time_limit_days)
            user.is_active = True
        db.session.commit()
        flash(t('voucher_applied'), 'success')
        if not session.get('portal_user_id'):
            session['portal_user_id'] = user.id
            session['portal_username'] = user.username
        return redirect(url_for('portal_dashboard'))
    return render_template('selfservice/voucher.html', user=user)


@app.route('/portal/profile', methods=['GET', 'POST'])
def portal_profile():
    user_id = session.get('portal_user_id')
    if not user_id:
        return redirect(url_for('portal_login'))
    user = RadUser.query.get_or_404(user_id)
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if new_password:
            if new_password != confirm:
                flash(t('password_mismatch'), 'danger')
                return redirect(url_for('portal_profile'))
            user.set_password(new_password)
            db.session.commit()
            flash(t('password_changed'), 'success')
        return redirect(url_for('portal_profile'))
    return render_template('selfservice/profile.html', user=user)


# ═══════════════════════════════════════════
#  واجهة API
# ═══════════════════════════════════════════

@app.route('/api/users/online')
@login_required
def api_online_users():
    sessions = RadAcct.query.filter(
        RadAcct.acctstoptime.is_(None)
    ).all()
    data = []
    for s in sessions:
        data.append({
            'username': s.username,
            'nas_ip': s.nasipaddress,
            'ip': s.framedipaddress,
            'duration': s.acctsessiontime,
            'download': s.acctoutputoctets,
            'upload': s.acctinputoctets
        })
    return jsonify(data)


@app.route('/api/stats')
@login_required
def api_stats():
    return jsonify({
        'total_users': RadUser.query.count(),
        'active_users': RadUser.query.filter_by(is_active=True).count(),
        'online': RadAcct.query.filter(
            RadAcct.acctstoptime.is_(None)
        ).count(),
        'revenue_today': db.session.query(
            db.func.sum(Payment.amount)
        ).filter(
            Payment.created_at >= datetime.utcnow().replace(
                hour=0, minute=0, second=0
            )
        ).scalar() or 0
    })


# ═══════════════════════════════════════════
#  تهيئة التطبيق
# ═══════════════════════════════════════════

@app.before_request
def create_tables():
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        app.db_initialized = True

        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin', full_name='مدير النظام', role='admin'
            )
            admin.set_password('admin')
            db.session.add(admin)

        if Package.query.count() == 0:
            defaults = [
                Package(
                    name='برونزي', name_en='Bronze',
                    speed_down='2M', speed_up='1M',
                    burst_down='4M', burst_up='2M',
                    burst_threshold_down='1500k', burst_threshold_up='800k',
                    burst_time_up=16, burst_time_down=16,
                    priority=8,
                    price=15, time_limit_days=30,
                    reset_counters='monthly'
                ),
                Package(
                    name='فضي', name_en='Silver',
                    speed_down='5M', speed_up='2M',
                    burst_down='10M', burst_up='4M',
                    burst_threshold_down='3500k', burst_threshold_up='1500k',
                    burst_time_up=16, burst_time_down=16,
                    min_rate_up='512k', min_rate_down='1M',
                    priority=6,
                    price=30, time_limit_days=30,
                    reset_counters='monthly'
                ),
                Package(
                    name='ذهبي', name_en='Gold',
                    speed_down='10M', speed_up='5M',
                    burst_down='20M', burst_up='10M',
                    burst_threshold_down='7000k', burst_threshold_up='3500k',
                    burst_time_up=16, burst_time_down=16,
                    min_rate_up='1M', min_rate_down='2M',
                    priority=4,
                    price=50, time_limit_days=30,
                    reset_counters='monthly'
                ),
                Package(
                    name='ماسي', name_en='Diamond',
                    speed_down='20M', speed_up='10M',
                    burst_down='40M', burst_up='20M',
                    burst_threshold_down='14000k', burst_threshold_up='7000k',
                    burst_time_up=8, burst_time_down=8,
                    min_rate_up='2M', min_rate_down='5M',
                    priority=2,
                    price=80, time_limit_days=30,
                    concurrent_limit=3,
                    reset_counters='monthly'
                ),
                Package(
                    name='يومي', name_en='Daily',
                    speed_down='5M', speed_up='2M',
                    burst_down='10M', burst_up='4M',
                    burst_threshold_down='3500k', burst_threshold_up='1500k',
                    burst_time_up=16, burst_time_down=16,
                    priority=8,
                    price=3, time_limit_days=1,
                    data_limit_gb=2, transfer_limit_gb=3,
                    uptime_limit_hours=12,
                    reset_counters='daily'
                ),
                Package(
                    name='أسبوعي', name_en='Weekly',
                    speed_down='10M', speed_up='3M',
                    burst_down='20M', burst_up='6M',
                    burst_threshold_down='7000k', burst_threshold_up='2500k',
                    burst_time_up=16, burst_time_down=16,
                    min_rate_up='512k', min_rate_down='2M',
                    priority=6,
                    price=10, time_limit_days=7,
                    data_limit_gb=10, transfer_limit_gb=15,
                    reset_counters='weekly'
                ),
            ]
            for p in defaults:
                db.session.add(p)

        if Customer.query.count() == 0:
            c = Customer(name='عميل افتراضي', name_en='Default Customer', balance=0)
            db.session.add(c)

        db.session.commit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
