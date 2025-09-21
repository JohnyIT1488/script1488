#!/bin/bash
set -e

# Базовые пакеты
apt update && apt upgrade -y
apt install -y curl wget git ufw htop unzip

# Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER
apt install -y docker-compose-plugin

# Firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Nginx + Certbot
apt install -y nginx certbot python3-certbot-nginx

# Мониторинг: Prometheus + Node Exporter + Grafana
mkdir -p /opt/monitoring
cd /opt/monitoring
cat > docker-compose.yml <<'EOF'
version: "3.8"
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  node-exporter:
    image: prom/node-exporter
    ports:
      - "9100:9100"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana-data:/var/lib/grafana
volumes:
  grafana-data:
EOF

cat > prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

docker compose up -d

# GoAccess для анализа логов Nginx
apt install -y goaccess
echo 'Теперь можешь смотреть статистику: goaccess /var/log/nginx/access.log -o /var/www/html/report.html --log-format=COMBINED --real-time-html'
