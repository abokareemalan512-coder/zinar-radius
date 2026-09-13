#!/bin/bash
set -e

# ═══════════════════════════════════════════
#  🔐 زنار — Startup Script
#  Starts Flask on port 1892 + optional
#  Cloudflare tunnel for public access
# ═══════════════════════════════════════════

PORT=${ZINAR_PORT:-1892}
TUNNEL=${ZINAR_TUNNEL:-1}
TUNNEL_LOG=/tmp/cloudflared.log
FLASK_LOG=/tmp/flask.log

# ─── Initialize Database ───
if [ ! -f /app/instance/zinar.db ]; then
    echo "📦 Initializing database..."
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
        print('✅ Admin account created (admin/admin)')
"
fi

# ─── Start Flask ───
echo "🚀 Starting Zinar on port $PORT..."
python3 run.py > $FLASK_LOG 2>&1 &
FLASK_PID=$!
sleep 3

# ─── Start Cloudflare Tunnel ───
if [ "$TUNNEL" = "1" ]; then
    echo "🌐 Starting Cloudflare tunnel..."
    cloudflared tunnel --url http://localhost:$PORT > $TUNNEL_LOG 2>&1 &
    TUNNEL_PID=$!
    
    # Wait for tunnel URL
    echo "⏳ Waiting for public URL..."
    URL=""
    for i in $(seq 1 60); do
        URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' $TUNNEL_LOG 2>/dev/null | head -1)
        if [ -n "$URL" ]; then
            break
        fi
        sleep 2
    done
    
    if [ -n "$URL" ]; then
        echo ""
        echo '╔════════════════════════════════════════════════════╗'
        echo '║  🔐 زنار — نظام RADIUS لإدارة المستخدمين          ║'
        echo '╠════════════════════════════════════════════════════╣'
        echo "║  🌐 Public URL: $URL"
        echo "║  🏠 Local URL:  http://localhost:$PORT/"
        echo '║  👤 Login:       admin / admin'
        echo '╚════════════════════════════════════════════════════╝'
        echo ""
        # Save URL for other processes
        echo "$URL" > /tmp/zinar_public_url.txt
    else
        echo "⚠️  Could not get tunnel URL (check $TUNNEL_LOG)"
    fi
else
    echo ""
    echo '╔════════════════════════════════════════════════════╗'
    echo '║  🔐 زنار — نظام RADIUS لإدارة المستخدمين          ║'
    echo '╠════════════════════════════════════════════════════╣'
    echo "║  🏠 URL:  http://localhost:$PORT/"
    echo '║  👤 Login: admin / admin'
    echo '╚════════════════════════════════════════════════════╝'
    echo ""
fi

# ─── Keep Alive ───
echo "✅ System running. Press Ctrl+C to stop."

# Graceful shutdown
trap "echo 'Shutting down...'; kill $FLASK_PID 2>/dev/null; kill $TUNNEL_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Wait for Flask process
wait $FLASK_PID
