#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  زنار (Zinar) - RADIUS User Management System
#  Production Installation Script (systemd service)
# ═══════════════════════════════════════════════════════════
set -e

APP_DIR="/opt/zinar"
APP_USER="zinar"
PYTHON_BIN="python3"

APP_DIR_ESC="$(echo $APP_DIR | sed 's/\//\\\//g')"

echo "╔══════════════════════════════════════════╗"
echo "║   زنار (Zinar) RADIUS Management System   ║"
echo "║          Installation Script              ║"
echo "╚══════════════════════════════════════════╝"

# ─── 1. System Dependencies ───
echo "[1/8] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv sqlite3 libsqlite3-dev curl

# ─── 2. Create App User ───
echo "[2/8] Creating application user..."
id -u $APP_USER 2>/dev/null || useradd -r -s /bin/false $APP_USER

# ─── 3. Copy Files ───
echo "[3/8] Copying application files..."
mkdir -p $APP_DIR/instance $APP_DIR/static $APP_DIR/templates
cp -r . $APP_DIR/

# ─── 4. Python Virtual Environment ───
echo "[4/8] Setting up Python virtual environment..."
cd $APP_DIR
$PYTHON_BIN -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# ─── 5. Initialize Database ───
echo "[5/8] Initializing database..."
rm -f instance/zinar.db
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    from app import Admin
    a = Admin(username='admin')
    a.set_password('admin')
    db.session.add(a)
    db.session.commit()
    print('Admin user created (admin/admin)')
"
chmod 666 instance/zinar.db

# ─── 6. Install Cloudflared ───
echo "[6/8] Installing Cloudflare tunnel..."
ARCH=$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')
curl -L -k -o /usr/local/bin/cloudflared "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" 2>/dev/null
chmod +x /usr/local/bin/cloudflared 2>/dev/null || echo "cloudflared install skipped"

# ─── 7. Permissions ───
echo "[7/8] Setting permissions..."
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod 666 $APP_DIR/instance/zinar.db

# ─── 8. Systemd Services ───
echo "[8/8] Installing systemd services..."

cat > /etc/systemd/system/zinar.service << 'SVCEOF'
[Unit]
Description=Zinar RADIUS Management System
After=network.target

[Service]
Type=simple
User=zinar
WorkingDirectory=/opt/zinar
ExecStart=/opt/zinar/venv/bin/gunicorn -w 2 -b 0.0.0.0:1892 run:app
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/zinar
Environment=ZINAR_PORT=1892
Environment=ZINAR_HOST=0.0.0.0
Environment=ZINAR_PREFIX=

[Install]
WantedBy=multi-user.target
SVCEOF

cat > /etc/systemd/system/zinar-tunnel.service << 'TNLEOF'
[Unit]
Description=Zinar Cloudflare Tunnel
After=network.target zinar.service
Requires=zinar.service

[Service]
Type=simple
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:1892
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
TNLEOF

systemctl daemon-reload
systemctl enable zinar
systemctl start zinar
systemctl enable zinar-tunnel
systemctl start zinar-tunnel

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║          Installation Complete!           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  🌐 Admin Panel:  http://YOUR_SERVER:1892/"
echo "  👤 Default Login: admin / admin"
echo "  📡 RADIUS Auth:  port 1812"
echo "  📡 RADIUS Acct:  port 1813"
echo "  📡 CoA Port:     port 3799"
echo ""
echo "  🌐 Public URL: check journalctl -u zinar-tunnel"
echo "  ⚠️  Change the admin password after first login!"
echo "  📄 Flask:   systemctl status zinar"
echo "  📄 Tunnel:   systemctl status zinar-tunnel"
echo "  📄 Logs:    journalctl -u zinar -f"
