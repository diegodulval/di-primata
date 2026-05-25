#!/usr/bin/env bash
# Configuração inicial do droplet — roda uma vez.
# Uso: make bootstrap-droplet
set -euo pipefail

SSH="ssh -i digital-ocean -o StrictHostKeyChecking=no"
HOST="root@67.205.129.68"

echo "── Bootstrap do droplet ─────────────────────────────────"
$SSH $HOST bash <<'REMOTE'
set -euo pipefail

echo "▸ Swap 2GB"
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "  criado."
else
    echo "  já existe: $(swapon --show | tail -1)"
fi

echo "▸ Docker"
if ! command -v docker &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    echo "  instalado: $(docker --version)"
else
    echo "  já instalado: $(docker --version)"
fi

mkdir -p /app
echo ""
echo "✓ Droplet pronto."
echo ""
echo "  Próximos passos:"
echo "  1. Crie /app/.env com as variáveis de produção (ver .env.prod.example)"
echo "  2. Execute: make deploy"
echo "  3. Execute: make migrate-droplet"
REMOTE
