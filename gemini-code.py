"""
════════════════════════════════════════════════════════════
  🔐 منصة زنار RADIUS — المحرك المكتمل المربوط بـ Render
════════════════════════════════════════════════════════════
"""
import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('ZINAR_SECRET_KEY', 'zinar-radius-production-key-2026')

# ربط قاعدة البيانات الدائمة لـ PostgreSQL لمنع مسح البيانات على Render
db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'zinar.db'))
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'), exist_ok=True)
db = SQLAlchemy(app)

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), default='مدير النظام')

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

class RadUser(db.Model):
    __tablename__ = 'rad_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class NASDevice(db.Model):
    __tablename__ = 'nas_devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False, unique=True)
    shared_secret = db.Column(db.String(100), nullable=False)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return redirect(url_for('dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    total_users = RadUser.query.count()
    total_nas = NASDevice.query.count()
    admin = Admin.query.get(session['admin_id'])
    return render_template('dashboard.html', total_users=total_users, total_nas=total_nas, admin=admin)

# المسار الحقيقي لتعديل الحساب من المنصة المباشرة
@app.route('/admin/update-profile', methods=['POST'])
@login_required
def update_profile():
    admin = Admin.query.get(session['admin_id'])
    data = request.get_json() if request.is_json else request.form

    new_username = data.get('username', '').strip()
    new_password = data.get('password', '').strip()

    if new_username:
        existing = Admin.query.filter_by(username=new_username).first()
        if existing and existing.id != admin.id:
            return jsonify({'success': False, 'message': 'اسم المستخدم هذا مستخدم بالفعل'}), 400
        admin.username = new_username
        session['admin_username'] = new_username

    if new_password:
        admin.set_password(new_password)

    db.session.commit()
    return jsonify({'success': True, 'message': 'تم تحديث البيانات بنجاح!'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.before_request
def init_db():
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        app.db_initialized = True
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', full_name='مدير النظام')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('ZINAR_PORT', 1892))
    app.run(host='0.0.0.0', port=port, debug=False)