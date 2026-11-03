FROM python:3.12-slim

# Install nginx for serving the landing page + static video
RUN apt-get update && apt-get install -y --no-install-recommends nginx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ── Nginx config: serve index.html + static/ on port 80 ──────────────────────
RUN cat > /etc/nginx/sites-enabled/default << 'EOF'
server {
    listen 80;
    root /app;
    index index.html;

    location /static/ {
        alias /app/static/;
        add_header Cache-Control "public, max-age=31536000";
        types { video/mp4 mp4; }
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

EXPOSE 80 8501

# Start nginx (landing page) + streamlit (dashboard) together
CMD nginx && streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
