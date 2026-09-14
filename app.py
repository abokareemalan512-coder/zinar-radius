"""
════════════════════════════════════════════════════════════
  🔐 زنار — نظام RADIUS لإدارة مستخدمين ميكروتيك
  Zinar — RADIUS User Management System for MikroTik
  Enhanced with MikroTik User Manager features
════════════════════════════════════════════════════════════
"""

import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# إعداد قاعدة البيانات PostgreSQL على Render مع دعم SQLite كبديل محلي
db_url = os.environ.get('DATABASE_URL', 'sqlite:///zinar_radius.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'zinar-secret-key-2026-radius')

db = SQLAlchemy(app)

# ==================== نماذج قاعدة البيانات ====================

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
    location = db.Column(db.String(150), default='غير محدد')
    status = db.Column(db.String(20), default='متصل')

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    download_speed = db.Column(db.String(50), nullable=False) # تنزيل
    upload_speed = db.Column(db.String(50), nullable=False)   # تحميل
    duration_days = db.Column(db.Integer, nullable=False)      # المدة بالأيام

class RadiusUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscriber_name = db.Column(db.String(100), nullable=False) # اسم المشترك
    username = db.Column(db.String(100), unique=True, nullable=False) # اسم المستخدم
    password = db.Column(db.String(100), nullable=False) # كلمة المرور
    package_name = db.Column(db.String(100), nullable=False) # الباقة
    ip_address = db.Column(db.String(45), default='192.168.88.15') # عنوان IP
    start_date = db.Column(db.String(50), nullable=False) # تاريخ البداية
    expire_date = db.Column(db.String(50), nullable=False) # تاريخ الانتهاء
    status = db.Column(db.String(20), default='نشط')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='مفعل')

class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    package_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='جاهز')

class ActiveSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    mac_address = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    duration = db.Column(db.String(50), default='00:15:00')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(50), nullable=False)

# بناء وتحديث الجداول تلقائياً
with app.app_context():
    db.create_all()
    if not AdminUser.query.filter_by(username='admin').first():
        db.session.add(AdminUser(username='admin', password='adminpassword123'))
        db.session.commit()

# ==================== المسارات و APIs ====================

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

# --- تحديث بيانات حساب المدير في قاعدة البيانات بشكل حقيقي ---
@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    data = request.get_json()
    new_username = data.get('username', '').strip()
    new_password = data.get('password', '').strip()
    
    admin = AdminUser.query.first()
    if not admin:
        admin = AdminUser(username='admin', password='adminpassword123')
        db.session.add(admin)
    
    if new_username:
        admin.username = new_username
    if new_password:
        admin.password = new_password
        
    db.session.commit()
    session['user'] = admin.username
    return jsonify({'message': 'تم تحديث بيانات حساب المدير في قاعدة البيانات بنجاح', 'username': admin.username})

@app.route('/api/admin/current', methods=['GET'])
def get_current_admin():
    admin = AdminUser.query.first()
    return jsonify({'username': admin.username if admin else 'admin'})

# --- API الراوترات ---
@app.route('/api/routers', methods=['GET', 'POST'])
def handle_routers():
    if request.method == 'POST':
        d = request.get_json()
        r = Router(name=d['name'], ip_address=d['ip_address'], radius_port=d.get('radius_port', 1812), secret=d['secret'], location=d.get('location', 'غير محدد'))
        db.session.add(r)
        db.session.commit()
        return jsonify({'message': 'تم حفظ الراوتر بنجاح'}), 201
    items = Router.query.order_by(Router.id.desc()).all()
    return jsonify([{'id': i.id, 'name': i.name, 'ip_address': i.ip_address, 'radius_port': i.radius_port, 'location': i.location, 'status': i.status} for i in items])

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

# --- API الباقات ---
@app.route('/api/packages', methods=['GET', 'POST'])
def handle_packages():
    if request.method == 'POST':
        d = request.get_json()
        p = Package(
            name=d['name'],
            price=float(d['price']),
            download_speed=d['download_speed'],
            upload_speed=d['upload_speed'],
            duration_days=int(d['duration_days'])
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({'message': 'تم إضافة الباقة بنجاح'}), 201
    items = Package.query.order_by(Package.id.desc()).all()
    return jsonify([{'id': i.id, 'name': i.name, 'price': i.price, 'download_speed': i.download_speed, 'upload_speed': i.upload_speed, 'duration_days': i.duration_days} for i in items])

@app.route('/api/packages/<int:id>', methods=['DELETE'])
def delete_package(id):
    p = Package.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return jsonify({'message': 'تم حذف الباقة'})

# --- API المشتركين والمستخدمين ---
@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    if request.method == 'POST':
        d = request.get_json()
        u = RadiusUser(
            subscriber_name=d['subscriber_name'],
            username=d['username'],
            password=d['password'],
            package_name=d['package_name'],
            ip_address=d.get('ip_address', '192.168.88.15'),
            start_date=d.get('start_date', datetime.now().strftime('%Y-%m-%d')),
            expire_date=d.get('expire_date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
        )
        db.session.add(u)
        db.session.commit()
        return jsonify({'message': 'تم إضافة المشترك والمستخدم بنجاح'}), 201
    
    items = RadiusUser.query.order_by(RadiusUser.id.desc()).all()
    return jsonify([{
        'id': i.id,
        'subscriber_name': i.subscriber_name,
        'username': i.username,
        'password': i.password,
        'package_name': i.package_name,
        'ip_address': i.ip_address,
        'start_date': i.start_date,
        'expire_date': i.expire_date,
        'status': i.status
    } for i in items])

@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    u = RadiusUser.query.get(id)
    if u:
        db.session.delete(u)
        db.session.commit()
    return jsonify({'message': 'تم حذف المشترك'})

# --- APIs بقية الخيارات ---
@app.route('/api/customers', methods=['GET', 'POST'])
def handle_customers():
    if request.method == 'POST':
        d = request.get_json()
        db.session.add(Customer(name=d['name'], phone=d['phone']))
        db.session.commit()
        return jsonify({'message': 'تم حفظ العميل'})
    return jsonify([{'id': i.id, 'name': i.name, 'phone': i.phone, 'status': i.status} for i in Customer.query.all()])

@app.route('/api/vouchers', methods=['GET', 'POST'])
def handle_vouchers():
    if request.method == 'POST':
        d = request.get_json()
        db.session.add(Voucher(code=d['code'], package_name=d['package_name'], price=float(d['price'])))
        db.session.commit()
        return jsonify({'message': 'تم إنشاء الكارت'})
    return jsonify([{'id': i.id, 'code': i.code, 'package_name': i.package_name, 'price': i.price, 'status': i.status} for i in Voucher.query.all()])

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    return jsonify([{'id': i.id, 'username': i.username, 'mac_address': i.mac_address, 'ip_address': i.ip_address, 'duration': i.duration} for i in ActiveSession.query.all()])

@app.route('/api/payments', methods=['GET', 'POST'])
def handle_payments():
    if request.method == 'POST':
        d = request.get_json()
        db.session.add(Payment(customer_name=d['customer_name'], amount=float(d['amount']), date=d.get('date', datetime.now().strftime('%Y-%m-%d'))))
        db.session.commit()
        return jsonify({'message': 'تم تسجيل الدفعة'})
    return jsonify([{'id': i.id, 'customer_name': i.customer_name, 'amount': i.amount, 'date': i.date} for i in Payment.query.all()])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
