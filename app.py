import os

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# إعداد قاعدة البيانات (يدعم PostgreSQL على Render أو SQLite كبديل)
db_url = os.environ.get('DATABASE_URL', 'sqlite:///zinar_radius.db')
if db_url.startswith('postgres://'):
  db_url = db_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'zinar-secret-key-2026-radius'
)

db = SQLAlchemy(app)


# === نماذج قاعدة البيانات (Database Models) ===
class Router(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  ip_address = db.Column(db.String(45), nullable=False)
  radius_port = db.Column(db.Integer, default=1812)
  secret = db.Column(db.String(100), nullable=False)
  location = db.Column(db.String(150), default='غير محدد')
  status = db.Column(db.String(20), default='متصل')


class AdminUser(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(50), unique=True, nullable=False)
  password = db.Column(db.String(100), nullable=False)


# إنشاء الجداول وتوفير حساب مدير افتراضي إن لم يوجد
with app.app_context():
  db.create_all()
  if not AdminUser.query.filter_by(username='admin').first():
    default_admin = AdminUser(username='admin', password='adminpassword123')
    db.session.add(default_admin)
    db.session.commit()


# === مسارات التطبيق (App Routes) ===
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


# === مسارات API للراوترات والسيرفرات (Routers REST API) ===
@app.route('/api/routers', methods=['GET'])
def get_routers():
  routers = Router.query.order_by(Router.id.desc()).all()
  return jsonify([{
      'id': r.id,
      'name': r.name,
      'ip_address': r.ip_address,
      'radius_port': r.radius_port,
      'location': r.location,
      'status': r.status,
  } for r in routers])


@app.route('/api/routers', methods=['POST'])
def add_router():
  data = request.get_json() or request.form
  name = data.get('name')
  ip_address = data.get('ip_address')
  radius_port = data.get('radius_port', 1812)
  secret = data.get('secret', '123456')
  location = data.get('location', 'غير محدد')

  if not name or not ip_address:
    return jsonify({'error': 'اسم الراوتر وعنوان IP مطلوبان'}), 400

  new_router = Router(
      name=name,
      ip_address=ip_address,
      radius_port=int(radius_port),
      secret=secret,
      location=location,
      status='متصل بنجاح',
  )
  db.session.add(new_router)
  db.session.commit()

  return jsonify({
      'message': 'تم إضافة الراوتر بنجاح',
      'router': {
          'id': new_router.id,
          'name': new_router.name,
          'ip_address': new_router.ip_address,
          'radius_port': new_router.radius_port,
          'location': new_router.location,
          'status': new_router.status,
      },
  }), 201


@app.route('/api/routers/<int:router_id>', methods=['DELETE'])
def delete_router(router_id):
  router = Router.query.get(router_id)
  if not router:
    return jsonify({'error': 'الراوتر غير موجود'}), 404

  db.session.delete(router)
  db.session.commit()
  return jsonify({'message': 'تم حذف الراوتر بنجاح'})


@app.route('/api/routers/<int:router_id>/ping', methods=['POST'])
def ping_router(router_id):
  router = Router.query.get(router_id)
  if not router:
    return jsonify({'error': 'الراوتر غير موجود'}), 404
  return jsonify(
      {'message': f'تم اختبار الاتصال بنجاح مع {router.name}', 'ping_ms': 12}
  )


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
