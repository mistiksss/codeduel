#!/bin/bash
set -e

echo "=== CodeDuel Deploy Script ==="

echo "[1/8] Создание пользователя..."
if ! id "codeduel" &>/dev/null; then
    sudo useradd -r -s /bin/false -d /opt/codeduel codeduel
fi

echo "[2/8] Установка пакетов..."
sudo apt update
sudo apt install -y \
    python3-venv python3-pip git nginx certbot python3-certbot-nginx \
    postgresql postgresql-contrib

echo "[3/8] PostgreSQL..."
sudo -u postgres psql -c "CREATE USER codeduel WITH PASSWORD '54321';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE codeduel_db OWNER codeduel;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER codeduel CREATEDB;" 2>/dev/null || true

echo "[4/8] Релиз..."
if [ -d /opt/codeduel/.git ]; then
    cd /opt/codeduel && sudo -u codeduel git pull
else
    sudo mkdir -p /opt/codeduel
    sudo git clone https://github.com/mistiksss/codeduel.git /opt/codeduel
fi
sudo chown -R codeduel:codeduel /opt/codeduel

# 5. Python зависимости
echo "[5/8] Python..."
cd /opt/codeduel
python3 -m venv venv
if [ -f /opt/codeduel/requirements.txt ]; then
    /opt/codeduel/venv/bin/pip install -r requirements.txt
fi

# 6. .env
echo "[6/8] Конфигурация..."
if [ ! -f /opt/codeduel/.env ]; then
    if [ -f /opt/codeduel/.env.example ]; then
        sudo cp /opt/codeduel/.env.example /opt/codeduel/.env
    fi
    echo ">>> ОТРЕДАКТИРУЙТЕ /opt/codeduel/.env <<<"
    echo "   SECRET_KEY=..."
    echo "   DATABASE_URL=postgresql://codeduel:54321@localhost:5432/codeduel_db"
fi

echo "[7/8] systemd..."
sudo cp /opt/codeduel/codeduel.service /etc/systemd/system/
sudo cp /opt/codeduel/gunicorn.conf.py /opt/codeduel/
sudo systemctl daemon-reload
sudo systemctl enable codeduel

echo "[8/8] Nginx..."
if [ -f /opt/codeduel/nginx.conf.example ]; then
    sudo cp /opt/codeduel/nginx.conf.example /etc/nginx/sites-available/codeduel
fi
sudo ln -sf /etc/nginx/sites-available/codeduel /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "=== Готово. Далее вручную ==="
echo "1. sudo nano /etc/nginx/sites-available/codeduel  — впишите YOUR_DOMAIN_HERE"
echo "2. sudo certbot --nginx -d YOUR_DOMAIN"
echo "3. sudo systemctl restart codeduel"
echo "4. sudo ufw allow 'Nginx Full'"
echo ""
echo "Логи: sudo journalctl -u codeduel -f"