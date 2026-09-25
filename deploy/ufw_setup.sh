#!/bin/bash
# ==============================================================================
# Linux UFW (Uncomplicated Firewall) Production Security Configuration
# Opens ports 22 (SSH), 80 (HTTP), 443 (HTTPS) and closes all other inbound ports.
# ==============================================================================

set -e

echo "=== [1/4] Varsayılan Güvenlik Duvarı Politikaları Ayarlanıyor ==="
sudo ufw default deny incoming
sudo ufw default allow outgoing

echo "=== [2/4] İzin Verilen Servis Portları Tanımlanıyor ==="
# Port 22: Güvenli SSH bağlantısı
sudo ufw allow 22/tcp comment 'SSH Secure Administration'

# Port 80: HTTP web trafiği (HTTPS yönlendirmesi için)
sudo ufw allow 80/tcp comment 'HTTP Web Traffic'

# Port 443: HTTPS şifreli E-Fatura API trafiği
sudo ufw allow 443/tcp comment 'HTTPS Secure Encrypted API Traffic'

echo "=== [3/4] UFW Güvenlik Duvarı Aktifleştiriliyor ==="
sudo ufw --force enable

echo "=== [4/4] Güncel Güvenlik Duvarı Durumu: ==="
sudo ufw status verbose

echo ">>> UFW güvenlik duvarı yapılandırması başarıyla tamamlandı!"
