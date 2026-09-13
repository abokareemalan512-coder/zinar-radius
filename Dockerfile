FROM python:3.11-slim

LABEL maintainer="Zinar RADIUS"
LABEL description="زنار — نظام RADIUS لإدارة مستخدمي ميكروتيك"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install cloudflared for public tunnel
RUN curl -L -k -o /usr/local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    && chmod +x /usr/local/bin/cloudflared

# Workdir
WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Ensure instance dir exists for SQLite
RUN mkdir -p /app/instance

# Default env vars
ENV ZINAR_PORT=1892
ENV ZINAR_HOST=0.0.0.0
ENV ZINAR_PREFIX=""
ENV ZINAR_DEBUG=0
ENV ZINAR_TUNNEL=1

# Expose port
EXPOSE 1892

# Start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
