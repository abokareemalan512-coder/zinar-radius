class Router(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(100), nullable=False) # عنوان IP أو النطاق
    username = db.Column(db.String(50), default='admin')   # اسم مستخدم المايكروتك
    port = db.Column(db.Integer, default=8728)             # منفذ API
    password = db.Column(db.String(100), default='')       # كلمة مرور المايكروتك
    use_ssl = db.Column(db.Boolean, default=False)         # خيار API-SSL
    location = db.Column(db.String(150), default='الفرع الرئيسي')
    status = db.Column(db.String(20), default='متصل')

@app.route('/api/routers', methods=['GET', 'POST'])
def handle_routers():
    if request.method == 'POST':
        d = request.get_json()
        new_router = Router(
            name=d.get('name', 'سيرفر المايكروتك'),
            ip_address=d.get('ip_address', ''),
            username=d.get('username', 'admin'),
            port=int(d.get('port', 8728)),
            password=d.get('password', ''),
            use_ssl=d.get('use_ssl', False),
            location=d.get('location', 'الفرع الرئيسي'),
            status='متصل'
        )
        db.session.add(new_router)
        db.session.commit()
        return jsonify({'message': 'تم حفظ بيانات السيرفر بنجاح'}), 201

    routers = Router.query.all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'ip_address': r.ip_address,
        'username': r.username,
        'port': r.port,
        'use_ssl': r.use_ssl,
        'location': r.location,
        'status': r.status
    } for r in routers])
