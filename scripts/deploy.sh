#!/usr/bin/env bash
# Deploy do di-auto (oficinas) no droplet Digital Ocean.
# Uso: make deploy
set -euo pipefail

SSH_KEY="digital-ocean"
HOST="root@67.205.129.68"
REMOTE_DIR="/app"

# Garante que estamos na raiz do projeto
cd "$(git rev-parse --show-toplevel)"

echo "── 1/3 Build do frontend ────────────────────────────────"
cd web && pnpm --filter oficinas build && cd ..
echo "  ✓ web/apps/oficinas/dist/"

echo ""
echo "── 2/3 Sincronizando código ─────────────────────────────"
rsync -az --delete \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='node_modules' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    --exclude='.env' \
    --exclude='digital-ocean' \
    --exclude='digital-ocean.pub' \
    --exclude='web/apps/dashboard' \
    --exclude='web/apps/portal' \
    --exclude='web/node_modules' \
    -e "ssh -i $SSH_KEY" \
    . "$HOST:$REMOTE_DIR/"

echo "  ✓ código sincronizado"

echo ""
echo "── 3/3 Iniciando serviços ───────────────────────────────"
ssh -i "$SSH_KEY" "$HOST" bash <<'REMOTE'
set -euo pipefail
cd /app

if [ ! -f .env ]; then
    echo "ERRO: /app/.env não encontrado!"
    echo "Crie o arquivo antes do deploy. Ver .env.prod.example"
    exit 1
fi

docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "── Status ───────────────────────────────────────────────"
sleep 5
docker compose -f docker-compose.prod.yml ps
REMOTE

echo ""
echo "✓ Deploy concluído → http://67.205.129.68"
echo ""
echo "  Se for o primeiro deploy, rode também:"
echo "  make migrate-droplet"
