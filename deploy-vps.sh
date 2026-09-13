#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  🔐 زنار (Zinar) — One-Command VPS Deployment Script
#  
#  Usage:  bash deploy-vps.sh
#  
#  This script:
#  1. Installs Python3, pip, cloudflared
#  2. Sets up virtual environment
#  3. Installs dependencies
#  4. Initializes database with admin account
#  5. Starts Flask on port 1892
#  6. Starts Cloudflare tunnel for public access
#  7. Shows the public URL!
#
#  For production, consider:
#  - Using systemd (see install.sh)
#  - Using Docker (see docker-compose.yml)
#  - Using a reverse proxy (nginx)
# ═══════════════════════════════════════════════════════════

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$APP_DIR/venv"
PORT=1892
TUNNEL_LOG="$APP_DIR/cloudflared.log"
FLASK_LOG="$APP_DIR/flask.log"
URL_FILE="$APP_DIR/zinar_url.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  🔐 زنار — نشر بنقرة واحدة                         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── 1. Check OS ───
echo -e "${YELLOW}[1/6]${NC} Checking system..."
if command -v python3 &>/dev/null; then
    echo "  ✅ Python3: $(python3 --version)"
else
    echo "  📦 Installing Python3..."
    if command -v apt-get &>/dev/null; then
        apt-get update -qq && apt-get install -y -qq python3 python3-pip python3-venv sqlite3
    elif command -v yum &>/dev/null; then
        yum install -y python3 python3-pip sqlite
    elif command -v dnf &>/dev/null; then
        dnf install -y python3 python3-pip sqlite
    else
        echo "  ❌ Unsupported OS. Install Python3 manually."
        exit 1
    fi
fi

# ─── 2. Cloudflared ───
echo -e "${YELLOW}[2/6]${NC} Setting up Cloudflare tunnel..."
if command -v cloudflared &>/dev/null; then
    echo "  ✅ cloudflared: $(cloudflared --version 2>&1 | head -1)"
else
    echo "  📦 Installing cloudflared..."
    ARCH=$(uname -m)
    case $ARCH in
        x86_64)  CF_ARCH="amd64" ;;
        aarch64) CF_ARCH="arm64" ;;
        *)       CF_ARCH="amd64" ;;
    esac
    curl -L -k -o /usr/local/bin/cloudflared \
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}" \
        && chmod +x /usr/local/bin/cloudflared
    echo "  ✅ cloudflared installed"
fi

# ─── 3. Virtual Environment ───
echo -e "${YELLOW}[3/6]${NC} Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$APP_DIR/requirements.txt"
echo "  ✅ Dependencies installed"

# ─── 4. Database ───
echo -e "${YELLOW}[4/6]${NC} Initializing database..."
cd "$APP_DIR"
rm -f instance/zinar.db
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
echo "  ✅ Database ready"

# ─── 5. Start Flask ───
echo -e "${YELLOW}[5/6]${NC} Starting Zinar on port $PORT..."
export ZINAR_PORT=$PORT
export ZINAR_HOST=0.0.0.0
export ZINAR_PREFIX=""
python3 run.py > "$FLASK_LOG" 2>&1 &
FLASK_PID=$!
sleep 3

if kill -0 $FLASK_PID 2>/dev/null; then
    echo "  ✅ Flask running (PID: $FLASK_PID)"
else
    echo "  ❌ Flask failed to start! Check $FLASK_LOG"
    cat "$FLASK_LOG"
    exit 1
fi

# ─── 6. Start Tunnel ───
echo -e "${YELLOW}[6/6]${NC} Starting Cloudflare tunnel..."
cloudflared tunnel --url http://localhost:$PORT > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

echo -e "${CYAN}  ⏳ Waiting for public URL...${NC}"
URL=""
for i in $(seq 1 60); do
    URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 2
done

if [ -n "$URL" ]; then
    echo "$URL" > "$URL_FILE"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ زنار يعمل بنجاح!                              ║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║  🌐 Public URL: $URL${NC}"
    echo -e "${GREEN}║  🏠 Local URL:  http://localhost:$PORT/${NC}"
    echo -e "${GREEN}║  👤 Login:       admin / admin${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  📝 URL saved to: $URL_FILE"
    echo "  📋 Flask PID: $FLASK_PID | Tunnel PID: $TUNNEL_PID"
    echo "  🛑 To stop: kill $FLASK_PID $TUNNEL_PID"
    echo ""
else
    echo "  ⚠️  Could not get tunnel URL. Check $TUNNEL_LOG"
    echo "  🏠 Local access: http://localhost:$PORT/"
fi

# Keep script running
wait $FLASK_PID
