#!/bin/bash
# ==============================================================================
# Production Deployment Automation Script for E-Invoice Integration API
# Target Environment: Ubuntu 22.04 / 24.04 LTS Linux VPS
# Architecture: FastAPI + Gunicorn (4 Workers) + Uvicorn + Nginx + Certbot + UFW
# ==============================================================================

set -e

APP_DIR="/var/www/einvoice-api"
DOMAIN="api.einvoice-erp.com"
EMAIL="admin@einvoice-erp.com"

echo "=== Adım 1: Linux Sistem Paketlerinin Güncellenmesi ==="
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx ufw certbot python3-certbot-nginx

echo "=== Adım 2: Güvenlik Duvarı (UFW) Yapılandırması ==="
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw --force enable
sudo ufw status verbose

echo "=== Adım 3: Uygulama Dizininin Hazırlanması ==="
sudo mkdir -p $APP_DIR
sudo mkdir -p /var/log/einvoice /var/log/nginx
sudo chown -R $USER:www-data $APP_DIR
sudo chmod -R 775 $APP_DIR

echo "=== Adım 4: Sanal Ortam ve Bağımlılıkların Kurulumu ==="
cd $APP_DIR
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Adım 5: Veritabanı Migrasyonları (Alembic) ve Seed Verisi ==="
alembic upgrade head
python seed.py

echo "=== Adım 6: Systemd Servis Dosyasının Konumlandırılması ==="
sudo cp deploy/einvoice.service /etc/systemd/system/einvoice.service
sudo systemctl daemon-reload
sudo systemctl enable einvoice
sudo systemctl restart einvoice

echo "=== Adım 7: Nginx Ters Vekil (Reverse Proxy) Yapılandırması ==="
sudo cp deploy/nginx.conf /etc/nginx/sites-available/einvoice
sudo ln -sf /etc/nginx/sites-available/einvoice /etc/nginx/sites-enabled/einvoice
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=== Adım 8: SSL/TLS Sertifikası (Certbot / Let's Encrypt) ==="
# Otomatik sertifika kurulumu ve Nginx HTTPS yönlendirmesi
# sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL --redirect

echo "=== Servis Durum Kontrolleri ==="
sudo systemctl status einvoice --no-pager
sudo systemctl status nginx --no-pager

echo ">>> E-Fatura API canlı sunucu ortamına başarıyla kuruldu ve başlatıldı!"
