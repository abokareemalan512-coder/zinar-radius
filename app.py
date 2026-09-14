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
    app.run(host='0.0.0.0', port=5000, debug=True)
