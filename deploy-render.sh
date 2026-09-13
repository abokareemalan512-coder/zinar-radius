#!/bin/bash
# ═══════════════════════════════════════════════════════
# 🔐 زنار v2 — سكربت نشر تلقائي على Render.com
# ═══════════════════════════════════════════════════════
# المتطلبات: git فقط
# الاستخدام: chmod +x deploy-render.sh && ./deploy-render.sh
# ═══════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║  🔐 زنار v2 — نشر تلقائي على Render.com       ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# ── التحقق من المتطلبات ──
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ git غير مثبت. ثبّته من: https://git-scm.com${NC}"
    exit 1
fi

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📌 الخطوة 1: إنشاء مستودع GitHub${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. اذهب إلى: https://github.com/new"
echo "2. اسم المستودع: zinar-radius"
echo "3. اختر Public"
echo "4. اضغط Create repository"
echo ""
read -p "✅ أنشأت المستودع؟ (y/n): " CREATED
if [ "$CREATED" != "y" ]; then
    echo "أنشئ المستودع أولًا ثم أعد تشغيل السكربت"
    exit 0
fi

echo ""
read -p "📝 اسم مستخدم GitHub (مثل: ahmed): " GH_USER
read -p "📧 بريد GitHub: " GH_EMAIL

git config --global user.name "$GH_USER"
git config --global user.email "$GH_EMAIL"

# ── إنشاء مشروع git ──
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📌 الخطوة 2: رفع المشروع لـ GitHub${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

git init
git add .
git commit -m "🔐 زنار v2 — Initial commit"
git branch -M main
git remote add origin https://github.com/${GH_USER}/zinar-radius.git
echo ""
echo -e "${GREEN}🚀 جاري الرفع...${NC}"
git push -u origin main

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📌 الخطوة 3: نشر على Render.com${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. اذهب إلى: https://dashboard.render.com"
echo "2. اضغط: New → Web Service"
echo "3. اربط حساب GitHub واختر مستودع zinar-radius"
echo "4. الإعدادات (تلقائية من render.yaml):"
echo "   • Runtime: Python"
echo "   • Build: pip install -r requirements.txt"
echo "   • Start: gunicorn -w 2 -b 0.0.0.0:$PORT run:app"
echo "5. أضف Environment Variable:"
echo "   • ZINAR_SECRET_KEY = (اضغط Generate)"
echo "6. اضغط Create Web Service ✅"
echo ""
echo -e "${GREEN}بعد 2-3 دقائق ستحصل على رابط مثل:${NC}"
echo -e "${CYAN}🔗 https://zinar-radius-xxxx.onrender.com${NC}"
echo ""
echo -e "${YELLOW}🔑 بيانات الدخول:${NC}"
echo "   اسم المستخدم: admin"
echo "   كلمة المرور: admin"
echo ""
echo -e "${RED}⚠️  غيّر كلمة المرور فوراً من صفحة الإعدادات!${NC}"
echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║  ✅ تم الرفع لـ GitHub بنجاح!                  ║"
echo "║  الآن أكمل على Render.com من الرابط أعلاه      ║"
echo "╚════════════════════════════════════════════════╝"
