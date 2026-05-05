#!/usr/bin/env bash
set -euo pipefail

DOMAIN="speedy.cardlabs.cloud"
EMAIL="barasapeter52@gmail.com"
REPO="https://github.com/barasapeter/BIKELEASE.git"
APP_DIR="/home/ubuntu/BIKELEASE"
DB_NAME="bikelease"
SERVICE_NAME="fastapi"
BIND_ADDR="127.0.0.1:8000"
# ==============================

# Provide password at runtime:
# sudo POSTGRES_PASSWORD='SuperStrongPassword' ./bootstrap.sh
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

if [[ -z "${POSTGRES_PASSWORD}" ]]; then
  echo "ERROR: POSTGRES_PASSWORD is empty."
  echo "Run like: sudo POSTGRES_PASSWORD='SuperStrongPassword' ./bootstrap.sh"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

echo "==> System update"
sudo apt-get update -y
sudo apt-get upgrade -y

# Ubuntu usually has the SSM agent available, but don’t rely on “usually”. Make it explicit in your bootstrap.
echo "==> Install + start SSM agent"
sudo snap install amazon-ssm-agent --classic || sudo apt-get install -y amazon-ssm-agent
sudo systemctl enable --now amazon-ssm-agent || true

echo "==> Install packages"
sudo apt-get install -y \
  git nginx certbot python3-certbot-nginx \
  python3.12-venv build-essential python3-dev libpq-dev \
  postgresql postgresql-contrib \
  libgl1 libglib2.0-0t64 libsm6 libxrender1 libxext6

echo "==> Clone/update repo"
if [[ -d "$APP_DIR/.git" ]]; then
  sudo -u ubuntu git -C "$APP_DIR" pull
else
  sudo -u ubuntu git clone "$REPO" "$APP_DIR"
fi

echo "==> venv + requirements"
sudo -u ubuntu bash -lc "
  set -e
  cd '$APP_DIR'
  python3 -m venv venv
  source venv/bin/activate
  pip install -U pip
  pip install -r requirements.txt
"

echo "==> Write .env"
sudo -u ubuntu bash -lc "cat > '$APP_DIR/.env' <<EOF
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=${DB_NAME}

JWT_SECRET_KEY=this_is_a_placeholder_lol

AWS_ACCESS_KEY=lolno
AWS_SECRET_ACCESS_KEY=lol
EOF"


echo "==> Postgres: create db + set password (idempotent)"
sudo systemctl enable --now postgresql

# Create DB if missing
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  sudo -u postgres createdb "${DB_NAME}"
  echo "Created database: ${DB_NAME}"
else
  echo "Database already exists: ${DB_NAME}"
fi

# Set postgres password safely (escape single quotes)
ESCAPED_PW="${POSTGRES_PASSWORD//\'/\'\'}"
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "ALTER USER postgres WITH PASSWORD '${ESCAPED_PW}';"

echo "==> systemd service"
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null <<EOF
[Unit]
Description=FastAPI app (gunicorn)
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker apps.api.main:app --bind $BIND_ADDR
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"

echo "==> nginx config"
sudo tee /etc/nginx/sites-available/fastapi > /dev/null <<EOF
server {
    server_name $DOMAIN;

    location / {
        proxy_pass http://$BIND_ADDR;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/fastapi

# Optional: disable default site if it's enabled (prevents conflicts)
if [[ -e /etc/nginx/sites-enabled/default ]]; then
  sudo rm -f /etc/nginx/sites-enabled/default
fi

sudo nginx -t
sudo systemctl restart nginx

echo "==> HTTPS (requires DNS already pointing to this instance)"
sudo certbot --nginx \
  -d "$DOMAIN" \
  --non-interactive --agree-tos -m "$EMAIL" --redirect || true

echo "==> certbot timer"
sudo systemctl status certbot.timer --no-pager || true

echo "Done."
echo "Check:"
echo "  sudo systemctl status $SERVICE_NAME --no-pager"
echo "  sudo journalctl -u $SERVICE_NAME -n 80 --no-pager"
echo "  curl -I http://$DOMAIN"
echo "  curl -I https://$DOMAIN"

# deploy updates
chmod +x deploy.sh

echo "==> Install deploy helper"
sudo ln -sf "$APP_DIR/deploy.sh" /usr/local/bin/app-deploy
sudo chmod +x /usr/local/bin/app-deploy
