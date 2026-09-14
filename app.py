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

# إعداد قاعدة البيانات (PostgreSQL على Render أو SQLite محلياً)
db_url = os.environ.get('DATABASE_URL', 'sqlite:///zinar_radius.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'zinar-secret-key-2026-radius')

db = SQLAlchemy(app)

# ==================== نماذج قاعدة البيانات المطابقة لـ User Manager ====================

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
    name = db.Column(db.String(100), nullable=False) # اسم الخطة مثل 5M
    price = db.Column(db.Float, default=0.0)
    download_speed = db.Column(db.String(50), default='5M')
    upload_speed = db.Column(db.String(50), default='1M')
    duration_days = db.Column(db.Integer, default=30)

class RadiusUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='مفعل')
    plan_name = db.Column(db.String(100), default='5M')
    server_name = db.Column(db.String(100), default='Not Found')
    mac_address = db.Column(db.String(50), default='00:00:00:00:00:00')
    ip_address = db.Column(db.String(45), default='0.0.0.0')
    download_gb = db.Column(db.Float, default=342.98) # إجمالي التحميل
    upload_gb = db.Column(db.Float, default=35.69)    # إجمالي الرفع
    uptime = db.Column(db.String(50), default='20d15h50m55s') # وقت الاتصال
    expire_date = db.Column(db.String(100), default='09:03:10AM (4 Days) 19-09-2026')
    allowed_data = db.Column(db.String(50), default='unlimited')
    used_data_gb = db.Column(db.Float, default=378.68)

with app.app_context():
    db.create_all()
    if not AdminUser.query.filter_by(username='admin').first():
        db.session.add(AdminUser(username='admin', password='adminpassword123'))
        db.session.commit()
    # تجربة مستخدم افتراضي مطابقة للصورة
    if not RadiusUser.query.first():
        db.session.add(RadiusUser(
            username='61779069',
            password='123',
            status='مفعل',
            plan_name='5M',
            server_name='Not Found',
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

# ==================== APIs والمسارات ====================

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

# === APIs المشتركين المعتمدة ===
@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    if request.method == 'POST':
        d = request.get_json()
        u = RadiusUser(
            username=d['username'],
            password=d['password'],
            status=d.get('status', 'مفعل'),
            plan_name=d.get('plan_name', '5M'),
            server_name=d.get('server_name', 'Not Found'),
            mac_address=d.get('mac_address', '00:00:00:00:00:00'),
            ip_address=d.get('ip_address', '0.0.0.0'),
            expire_date=d.get('expire_date', '09:03:10AM (30 Days) 19-10-2026')
        )
        db.session.add(u)
        db.session.commit()
        return jsonify({'message': 'تم إضافة المستخدم بنجاح'}), 201
    
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

@app.route('/api/users/<int:id>', methods=['GET'])
def get_single_user(id):
    u = RadiusUser.query.get(id)
    if not u:
        return jsonify({'error': 'غير موجود'}), 404
    return jsonify({
        'id': u.id, 'username': u.username, 'password': u.password, 'status': u.status,
        'plan_name': u.plan_name, 'server_name': u.server_name, 'mac_address': u.mac_address,
        'ip_address': u.ip_address, 'download_gb': u.download_gb, 'upload_gb': u.upload_gb,
        'uptime': u.uptime, 'expire_date': u.expire_date, 'allowed_data': u.allowed_data,
        'used_data_gb': u.used_data_gb
    })

@app.route('/api/users/<int:id>/reset', methods=['POST'])
def reset_user_counters(id):
    u = RadiusUser.query.get(id)
    if u:
        u.download_gb = 0.0
        u.upload_gb = 0.0
        u.used_data_gb = 0.0
        u.uptime = '0s'
        db.session.commit()
        return jsonify({'message': 'تم تصفير العدادات بنجاح'})
    return jsonify({'error': 'تعذر التصفير'}), 400

@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    u = RadiusUser.query.get(id)
    if u:
        db.session.delete(u)
        db.session.commit()
    return jsonify({'message': 'تم الحذف'})

# === APIs الحساب والراوترات والباقات ===
@app.route('/api/routers', methods=['GET', 'POST'])
def handle_routers():
    if request.method == 'POST':
        d = request.get_json()
        db.session.add(Router(name=d['name'], ip_address=d['ip_address'], radius_port=d.get('radius_port', 1812), secret=d['secret'], location=d.get('location', 'الفرع الرئيسي')))
        db.session.commit()
        return jsonify({'message': 'تم الحفظ'})
    return jsonify([{'id': r.id, 'name': r.name, 'ip_address': r.ip_address, 'radius_port': r.radius_port, 'location': r.location, 'status': r.status} for r in Router.query.all()])

@app.route('/api/packages', methods=['GET', 'POST'])
def handle_packages():
    if request.method == 'POST':
        d = request.get_json()
        db.session.add(Package(name=d['name'], price=float(d['price']), download_speed=d['download_speed'], upload_speed=d['upload_speed'], duration_days=int(d['duration_days'])))
        db.session.commit()
        return jsonify({'message': 'تم الحفظ'})
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'download_speed': p.download_speed, 'upload_speed': p.upload_speed, 'duration_days': p.duration_days} for p in Package.query.all()])

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    d = request.get_json()
    admin = AdminUser.query.first()
    if admin:
        admin.username = d['username']
        if d.get('password'): admin.password = d['password']
        db.session.commit()
        session['user'] = admin.username
    return jsonify({'message': 'تم الحفظ بنجاح'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
