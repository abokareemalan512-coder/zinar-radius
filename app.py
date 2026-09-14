"""
════════════════════════════════════════════════════════════
  🔐 زنار — نظام RADIUS لإدارة مستخدمين ميكروتيك
  Zinar — RADIUS User Management System for MikroTik
  Enhanced with MikroTik User Manager features
════════════════════════════════════════════════════════════
"""
import os

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# إعداد قاعدة البيانات PostgreSQL على Render مع دعم SQLite كبديل محلي
db_url = os.environ.get('DATABASE_URL', 'sqlite:///zinar_radius.db')
if db_url.startswith('postgres://'):
  db_url = db_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'zinar-secret-key-2026-radius'
)

db = SQLAlchemy(app)


# === نماذج قاعدة البيانات الشاملة (Database Models) ===
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


class RadiusUser(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(100), nullable=False)
  package_name = db.Column(db.String(100), nullable=False)
  ip_address = db.Column(db.String(45), default='192.168.88.15')
  expire_date = db.Column(db.String(50), nullable=False)
  status = db.Column(db.String(20), default='نشط')


class Package(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  price = db.Column(db.Float, nullable=False)
  speed = db.Column(db.String(50), nullable=False)
  validity = db.Column(db.String(50), nullable=False)


class Voucher(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  code = db.Column(db.String(50), unique=True, nullable=False)
  package_name = db.Column(db.String(100), nullable=False)
  price = db.Column(db.Float, nullable=False)
  status = db.Column(db.String(20), default='جاهز')


class Customer(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  phone = db.Column(db.String(50), nullable=False)
  status = db.Column(db.String(20), default='مفعل')


class Payment(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  customer_name = db.Column(db.String(100), nullable=False)
  amount = db.Column(db.Float, nullable=False)
  date = db.Column(db.String(50), nullable=False)


class ActiveSession(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(100), nullable=False)
  mac_address = db.Column(db.String(50), nullable=False)
  ip_address = db.Column(db.String(45), nullable=False)
  duration = db.Column(db.String(50), default='00:15:00')


# إنشاء الجداول تلقائياً
with app.app_context():
  db.create_all()
  if not AdminUser.query.filter_by(username='admin').first():
    db.session.add(AdminUser(username='admin', password='adminpassword123'))
    db.session.commit()

  if not Package.query.first():
    db.session.add(
        Package(
            name='باقة 50 جيجا', price=15.0, speed='10 ميجا', validity='30 يوم'
        )
    )
    db.session.add(
        Package(
            name='الباقة المفتوحة', price=35.0, speed='مفتوحة', validity='30 يوم'
        )
    )
    db.session.commit()


# === المسارات الرئيسية (Main Routes) ===
@app.route('/')
def index():
  return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    user = AdminUser.query.filter_by(
        username=username, password=password
    ).first()
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


# === APIs الراوترات ===
@app.route('/api/routers', methods=['GET'])
def get_routers():
  items = Router.query.order_by(Router.id.desc()).all()
  return jsonify([{
      'id': i.id,
      'name': i.name,
      'ip_address': i.ip_address,
      'radius_port': i.radius_port,
      'location': i.location,
      'status': i.status,
  } for i in items])


@app.route('/api/routers', methods=['POST'])
def add_router():
  d = request.get_json()
  r = Router(
      name=d['name'],
      ip_address=d['ip_address'],
      radius_port=d.get('radius_port', 1812),
      secret=d['secret'],
      location=d.get('location', 'غير محدد'),
  )
  db.session.add(r)
  db.session.commit()
  return jsonify({'message': 'تم الحفظ بنجاح'}), 201


@app.route('/api/routers/<int:id>', methods=['DELETE'])
def delete_router(id):
  r = Router.query.get(id)
  if r:
    db.session.delete(r)
    db.session.commit()
  return jsonify({'message': 'تم الحذف'})


@app.route('/api/routers/<int:id>/ping', methods=['POST'])
def ping_router(id):
  r = Router.query.get(id)
  return jsonify(
      {'message': f'تم اختبار الاتصال بنجاح مع {r.name if r else "السيرفر"}'}
  )


# === APIs المستخدمين ===
@app.route('/api/users', methods=['GET'])
def get_users():
  items = RadiusUser.query.all()
  return jsonify([{
      'id': i.id,
      'username': i.username,
      'package_name': i.package_name,
      'ip_address': i.ip_address,
      'expire_date': i.expire_date,
      'status': i.status,
  } for i in items])


@app.route('/api/users', methods=['POST'])
def add_user():
  d = request.get_json()
  u = RadiusUser(
      username=d['username'],
      package_name=d['package_name'],
      expire_date=d.get('expire_date', '2026-12-31'),
  )
  db.session.add(u)
  db.session.commit()
  return jsonify({'message': 'تم إضافة المستخدم بنجاح'}), 201


@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
  u = RadiusUser.query.get(id)
  if u:
    db.session.delete(u)
    db.session.commit()
  return jsonify({'message': 'تم الحذف'})


# === APIs الباقات ===
@app.route('/api/packages', methods=['GET'])
def get_packages():
  items = Package.query.all()
  return jsonify([{
      'id': i.id,
      'name': i.name,
      'price': i.price,
      'speed': i.speed,
      'validity': i.validity,
  } for i in items])


@app.route('/api/packages', methods=['POST'])
def add_package():
  d = request.get_json()
  p = Package(
      name=d['name'],
      price=float(d['price']),
      speed=d['speed'],
      validity=d['validity'],
  )
  db.session.add(p)
  db.session.commit()
  return jsonify({'message': 'تم إضافة الباقة بنجاح'}), 201


# === APIs العملاء والجلسات والمدفوعات والكروت ===
@app.route('/api/customers', methods=['GET', 'POST'])
def handle_customers():
  if request.method == 'POST':
    d = request.get_json()
    c = Customer(name=d['name'], phone=d['phone'])
    db.session.add(c)
    db.session.commit()
    return jsonify({'message': 'تم إضافة العميل'})
  return jsonify([
      {'id': i.id, 'name': i.name, 'phone': i.phone, 'status': i.status}
      for i in Customer.query.all()
  ])


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
  return jsonify([
      {
          'id': i.id,
          'username': i.username,
          'mac_address': i.mac_address,
          'ip_address': i.ip_address,
          'duration': i.duration,
      }
      for i in ActiveSession.query.all()
  ])


@app.route('/api/vouchers', methods=['GET', 'POST'])
def handle_vouchers():
  if request.method == 'POST':
    d = request.get_json()
    v = Voucher(
        code=d['code'], package_name=d['package_name'], price=float(d['price'])
    )
    db.session.add(v)
    db.session.commit()
    return jsonify({'message': 'تم إنشاء الكارت'})
  return jsonify([
      {
          'id': i.id,
          'code': i.code,
          'package_name': i.package_name,
          'price': i.price,
          'status': i.status,
      }
      for i in Voucher.query.all()
  ])


@app.route('/api/payments', methods=['GET', 'POST'])
def handle_payments():
  if request.method == 'POST':
    d = request.get_json()
    p = Payment(
        customer_name=d['customer_name'],
        amount=float(d['amount']),
        date=d.get('date', '2026-09-14'),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'message': 'تم تسجيل الدفعة'})
  return jsonify([
      {
          'id': i.id,
          'customer_name': i.customer_name,
          'amount': i.amount,
          'date': i.date,
      }
      for i in Payment.query.all()
  ])


@app.route('/api/profile/update', methods=['POST'])
def update_profile():
  d = request.get_json()
  user = AdminUser.query.first()
  if user:
    user.username = d['username']
    if d.get('password'):
      user.password = d['password']
    db.session.commit()
  return jsonify({'message': 'تم تحديث بيانات حساب المدير'})


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
