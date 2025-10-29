#!/usr/bin/env bash
# Script de deploy para produção

set -euo pipefail

echo "🚀 Iniciando deploy..."

# Ativar ambiente virtual
source .venv/bin/activate

# Atualizar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt --upgrade

# Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Aplicar migrações
echo "🗄️  Aplicando migrações..."
python manage.py migrate --noinput

# Criar diretório de logs
mkdir -p logs

echo "✅ Deploy concluído!"
echo ""
echo "Para produção, configure:"
echo "  - DJANGO_SETTINGS_MODULE=DjangoProject.settings_prod"
echo "  - Servidor ASGI (Daphne ou Uvicorn)"
echo "  - Supervisor para Celery worker e beat"
echo "  - Nginx como proxy reverso"
