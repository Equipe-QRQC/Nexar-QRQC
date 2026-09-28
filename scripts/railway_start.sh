#!/bin/sh
# Inicialização no Railway (ou qualquer hospedagem com disco montado).
# Com um volume montado, banco, chave de sessão, arquivos enviados e CADs importados
# ficam nele e sobrevivem a cada novo deploy.
set -e
cd "$(dirname "$0")/.."

DATA_DIR="${DATA_DIR:-$RAILWAY_VOLUME_MOUNT_PATH}"
if [ -n "$DATA_DIR" ]; then
  mkdir -p "$DATA_DIR/uploads" "$DATA_DIR/cad_importados"
  # Arquivos que vêm no repositório (fichas das máquinas) entram no volume só na primeira vez
  cp -rn static/uploads/. "$DATA_DIR/uploads/" 2>/dev/null || true
  rm -rf static/uploads cad_importados
  ln -s "$DATA_DIR/uploads" static/uploads
  ln -s "$DATA_DIR/cad_importados" cad_importados
  export DATABASE_PATH="${DATABASE_PATH:-$DATA_DIR/qrqc.db}"
else
  echo "AVISO: sem volume montado — banco e arquivos se perdem a cada deploy." >&2
fi

# Base de demonstração: só cria se ainda não houver ocorrências (o script recusa caso contrário)
if [ "$SEED_DEMO" = "1" ]; then
  python scripts/seed_demo.py --sem-ia || true
fi

exec gunicorn app:app --bind "0.0.0.0:${PORT:-8080}" --workers 1 --threads 8 --timeout 180 \
  --access-logfile - --error-logfile -
