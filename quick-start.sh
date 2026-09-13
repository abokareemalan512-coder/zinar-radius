#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  🔐 زنار — Quick Start Script
#  Runs Flask + Cloudflare Tunnel for instant public access
#  
#  Usage:  bash quick-start.sh
#  Result: Public URL you can open in any browser!
# ═══════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ─── Colors ───
G='\033[0;32m'
C='\033[0;36m'
Y='\033[1;33m'
N='\033[0m'

echo ""
echo -e "${C}╔════════════════════════════════════════════════════╗${N}"
echo -e "${C}║  🔐 زنار — تشغيل سريع                             ║${N}"
echo -e "${C}╚════════════════════════════════════════════════════╝${N}"
echo ""

# ─── 1. Check Python ───
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${Y}Installing Python3...${N}"
    apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv 2>/dev/null || \
    yum install -y python3 python3-pip 2>/dev/null || \
    { echo "❌ Install Python3 first"; exit 1; }
fi

# ─── 2. Virtual Env ───
if [ ! -d "venv" ]; then
    echo -e "${Y}[1/4]${N} Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# ─── 3. Dependencies ───
echo -e "${Y}[2/4]${N} Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# ─── 4. Database ───
echo -e "${Y}[3/4]${N} Initializing database..."
if [ ! -f instance/zinar.db ]; then
    python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    from app import Admin
    if not Admin.query.filter_by(username='admin').first():
        a = Admin(username='admin')
        a.set_password('admin')
        db.session.add(a)
        db.session.commit()
        print('  ✅ Admin account created')
"
fi

# ─── 5. Cloudflared ───
echo -e "${Y}[4/4]${N} Setting up Cloudflare tunnel..."
if ! command -v cloudflared >/dev/null 2>&1; then
    ARCH=$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')
    echo "  📦 Installing cloudflared..."
    sudo curl -L -k -o /usr/local/bin/cloudflared \
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" \
        && sudo chmod +x /usr/local/bin/cloudflared 2>/dev/null || \
    echo "  ⚠️  Install cloudflared manually for tunnel"
fi

# ─── Start Flask ───
echo ""
echo -e "${G}🚀 Starting Zinar on port 1892...${N}"
export ZINAR_PORT=1892
export ZINAR_HOST=0.0.0.0
export ZINAR_PREFIX=""
export ZINAR_DEBUG=0
python3 run.py > flask.log 2>&1 &
FLASK_PID=$!
sleep 3

if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo "❌ Flask failed! Check flask.log"
    cat flask.log
    exit 1
fi
echo "  ✅ Flask running (PID: $FLASK_PID)"

# ─── Start Tunnel ───
if command -v cloudflared >/dev/null 2>&1; then
    echo -e "${G}🌐 Starting Cloudflare tunnel...${N}"
    cloudflared tunnel --url http://localhost:1892 > tunnel.log 2>&1 &
    TUNNEL_PID=$!
    
    echo -e "${C}  ⏳ Waiting for public URL...${N}"
    URL=""
    for i in $(seq 1 60); do
        URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' tunnel.log 2>/dev/null | head -1)
        [ -n "$URL" ] && break
        sleep 2
    done
    
    if [ -n "$URL" ]; then
        echo ""
        echo -e "${G}╔════════════════════════════════════════════════════╗${N}"
        echo -e "${G}║  🎉 زنار يعمل بنجاح!                              ║${N}"
        echo -e "${G}╠════════════════════════════════════════════════════╣${N}"
        echo -e "${G}║${N}  🌐 الرابط العام: ${C}$URL${N}"
        echo -e "${G}║${N}  🏠 الرابط المحلي: http://localhost:1892/"
        echo -e "${G}║${N}  👤 الدخول: admin / admin"
        echo -e "${G}╚════════════════════════════════════════════════════╝${N}"
        echo ""
        echo "  📋 للإيقاف: kill $FLASK_PID $TUNNEL_PID"
        echo ""
        echo "$URL" > zinar_url.txt
        
        # Keep alive
        wait $FLASK_PID
    else
        echo "  ⚠️  No tunnel URL found"
        echo "  🏠 Local: http://localhost:1892/"
        wait $FLASK_PID
    fi
else
    echo ""
    echo -e "${G}╔════════════════════════════════════════════════════╗${N}"
    echo -e "${G}║  🎉 زنار يعمل!                                     ║${N}"
    echo -e "${G}╠════════════════════════════════════════════════════╣${N}"
    echo -e "${G}║${N}  🏠 الوصول: http://localhost:1892/"
    echo -e "${G}║${N}  👤 الدخول: admin / admin"
    echo -e "${G}╚════════════════════════════════════════════════════╝${N}"
    echo ""
    echo "  💡 لتثبيت Cloudflare tunnel للحصول على رابط عام:"
    echo "     https://github.com/cloudflare/cloudflared/releases/latest"
    echo ""
    wait $FLASK_PID
fi
