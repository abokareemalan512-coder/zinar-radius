#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  🔐 زنار — Docker Deployment (Easiest Method)
#  
#  Usage:  bash deploy-docker.sh
#  
#  Requirements: Docker + Docker Compose installed
#  Result: Zinar running on http://localhost:1892
#         with public URL via Cloudflare tunnel
# ═══════════════════════════════════════════════════════════

set -e

# Check Docker
if ! command -v docker &>/dev/null; then
    echo "❌ Docker not found. Install it first:"
    echo "   curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null; then
    echo "❌ Docker Compose not found. Install it first."
    exit 1
fi

echo ""
echo "🔐 زنار — Docker Deployment"
echo ""

# Build and start
docker compose up -d --build

# Wait for startup
echo "⏳ Waiting for Zinar to start..."
sleep 10

# Get tunnel URL
URL_FILE=$(docker exec zinar-radius cat /tmp/zinar_public_url.txt 2>/dev/null || echo "")

if [ -n "$URL_FILE" ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════╗"
    echo "║  ✅ زنار يعمل بنجاح!                              ║"
    echo "╠════════════════════════════════════════════════════╣"
    echo "║  🌐 Public URL: $URL_FILE"
    echo "║  🏠 Local URL:  http://localhost:1892/"
    echo "║  👤 Login:       admin / admin"
    echo "╚════════════════════════════════════════════════════╝"
    echo ""
else
    # Try to get URL from logs
    URL=$(docker logs zinar-radius 2>&1 | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1 || echo "")
    if [ -n "$URL" ]; then
        echo ""
        echo "🌐 Public URL: $URL"
    else
        echo "⚠️  Tunnel URL not yet available. Check:"
        echo "   docker logs zinar-radius"
    fi
    echo "🏠 Local: http://localhost:1892/"
fi

echo ""
echo "📋 Commands:"
echo "   docker logs zinar-radius       # View logs"
echo "   docker stop zinar-radius        # Stop"
echo "   docker start zinar-radius       # Start again"
 echo "   docker compose down             # Remove"
