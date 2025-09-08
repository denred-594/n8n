#!/bin/bash

set -e

echo "📦 Updating system..."
apt update && apt upgrade -y

echo "🐳 Installing Docker & Docker Compose..."
apt install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  ufw \
  fail2ban

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "✅ Docker installed."
docker run hello-world

read -p "🔧 Install NVIDIA GPU support (y/N)? " install_gpu
if [[ "$install_gpu" == "y" || "$install_gpu" == "Y" ]]; then
  echo "🔌 Installing NVIDIA GPU support..."
  apt install -y nvidia-driver-535
  echo "➡️ Reboot required after script."
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

  apt update
  apt install -y nvidia-container-toolkit

  nvidia-ctk runtime configure --runtime=docker
  systemctl restart docker
fi

echo "🌐 Installing Nginx and Certbot for external access..."
apt install -y nginx python3-certbot-nginx

read -p "🔗 Enter domain name for n8n (leave empty for IP-only access): " domain_name

echo "🧾 Cloning n8n repo..."
cd /root
git clone https://github.com/denred-594/n8n.git || echo "❗ Repo existiert bereits"
cd n8n
if [ ! -d "local-ai-packaged" ]; then
  echo "❗ Verzeichnis /root/n8n/local-ai-packaged/ nicht gefunden. Bitte überprüfe das Repository."
  exit 1
fi
cd local-ai-packaged

echo "🛠️ Fixing docker-compose.yml (removing version attribute)..."
sed -i '/^version:/d' docker-compose.yml || echo "ℹ️ Keine version-Angabe gefunden oder bereits entfernt"

echo "🌐 Creating Docker networks demo and local-ai-packaged_demo..."
docker network rm demo 2>/dev/null || echo "ℹ️ Netzwerk demo wurde nicht gefunden, wird neu erstellt"
docker network create --label com.docker.compose.network=demo demo
docker network rm local-ai-packaged_demo 2>/dev/null || echo "ℹ️ Netzwerk local-ai-packaged_demo wurde nicht gefunden, wird neu erstellt"
docker network create --label com.docker.compose.network=demo local-ai-packaged_demo

echo "🔧 Checking for .env file with required environment variables..."
if [ ! -f ".env" ]; then
  echo "⚠️ .env file not found. Creating a template..."
  cat > .env <<EOF
POSTGRES_USER=n8n
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=n8n
N8N_ENCRYPTION_KEY=$(openssl rand -base64 32)
N8N_USER_MANAGEMENT_JWT_SECRET=$(openssl rand -base64 32)
EOF
  echo "⚠️ Created /root/n8n/local-ai-packaged/.env with secure values. Check and edit if needed."
fi

echo "🚀 Starting Docker container for n8n with CPU profile..."
docker compose --profile cpu up -d

echo "🔍 Checking if n8n container is running..."
if [ -z "$(docker ps -q -f name=n8n)" ]; then
  echo "❗ n8n container is not running. Checking logs..."
  docker compose logs n8n
  exit 1
fi

echo "🛡️ Setting up UFW firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5678/tcp
ufw allow 3000/tcp  # Für open-webui
ufw allow 3001/tcp  # Für flowise
ufw allow 5432/tcp  # Für postgres (falls extern benötigt)
ufw allow 6333/tcp  # Für qdrant
ufw allow 6334/tcp  # Für qdrant
ufw allow 5001/tcp  # Für custom-api
ufw --force enable

echo "🌐 Configuring Nginx as reverse proxy..."
# Entferne die Standard-Nginx-Konfiguration
rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/n8n <<EOF
server {
    listen 80;
    server_name ${domain_name:-_};

    location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
}
EOF

ln -sf /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/n8n
nginx -t || { echo "❗ Nginx configuration test failed. Check /etc/nginx/sites-available/n8n"; exit 1; }
systemctl reload nginx || { echo "❗ Failed to reload Nginx. Check logs: /var/log/nginx/error.log"; exit 1; }

if [[ -n "$domain_name" ]]; then
  echo "🔐 Setting up SSL with Let's Encrypt for $domain_name..."
  certbot --nginx -d "$domain_name" --non-interactive --agree-tos --email denny@redel-aisolutions.com || {
    echo "❗ Failed to obtain SSL certificate. Continuing with HTTP..."
  }
else
  echo "ℹ️ No domain provided. Access via server IP (HTTP:80, HTTPS:443 if manually configured)."
fi

echo "🔍 Testing Nginx connectivity to n8n..."
curl -I http://localhost:5678 || { echo "❗ Failed to connect to n8n on port 5678. Check container logs: docker compose logs n8n"; exit 1; }

echo "🛡️ Setting up Fail2Ban with Docker and Nginx log monitoring..."
cat > /etc/fail2ban/filter.d/docker-n8n.conf <<EOF
[Definition]
failregex = .*authentication failed.*
EOF

cat > /etc/fail2ban/filter.d/nginx-n8n.conf <<EOF
[Definition]
failregex = ^<HOST> -.*"(GET|POST).*/.*" (401|403|444) .*
EOF

cat > /etc/fail2ban/jail.local <<EOF
[docker-n8n]
enabled = true
filter = docker-n8n
logpath = /var/lib/docker/containers/*/*-json.log
maxretry = 5
findtime = 3600
bantime = 3600

[nginx-n8n]
enabled = true
filter = nginx-n8n
logpath = /var/log/nginx/access.log
maxretry = 5
findtime = 3600
bantime = 3600
EOF

systemctl restart fail2ban

echo "💾 Creating backup script..."
mkdir -p /backup

cat > /root/backup-n8n.sh <<'EOF'
#!/bin/bash
TIMESTAMP=$(date +%F_%T)
docker exec n8n n8n export:workflow --all > /backup/workflows_$TIMESTAMP.json
docker exec n8n n8n export:credentials --all > /backup/credentials_$TIMESTAMP.json
tar -czf /backup/n8n-data_$TIMESTAMP.tar.gz /root/n8n
EOF

chmod +x /root/backup-n8n.sh

echo "📆 Setting up daily cronjob for backup..."
(crontab -l 2>/dev/null; echo "0 3 * * * /root/backup-n8n.sh") | crontab -

echo "✅ Setup complete!"

echo ""
echo "🌐 Du kannst n8n jetzt aufrufen unter:"
echo "  - HTTP: http://<SERVER-IP>:80"
echo "  - Direct (no proxy): http://<SERVER-IP>:5678"
[[ -n "$domain_name" ]] && echo "  - HTTPS: https://$domain_name"
[[ "$install_gpu" == "y" || "$install_gpu" == "Y" ]] && echo "🔁 Jetzt bitte rebooten: 'reboot'"
echo "ℹ️ Other services:"
echo "  - Open-webui: http://<SERVER-IP>:3000"
echo "  - Flowise: http://<SERVER-IP>:3001"
echo "  - Qdrant: http://<SERVER-IP>:6333"
echo "  - Custom-api: http://<SERVER-IP>:5001"
