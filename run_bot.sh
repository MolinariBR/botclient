#!/bin/bash

# Script para executar o bot

cd "$(dirname "$0")"

# Verificar e parar instâncias existentes do bot
echo "🔍 Verificando instâncias existentes do bot..."
BOT_PROCESSES=$(pgrep -f "python main.py" || true)

if [ ! -z "$BOT_PROCESSES" ]; then
    echo "⚠️  Encontradas instâncias do bot rodando (PIDs: $BOT_PROCESSES)"
    echo "🛑 Parando instâncias existentes..."
    echo "$BOT_PROCESSES" | xargs kill -TERM 2>/dev/null || true
    sleep 2
    # Forçar kill se ainda estiver rodando
    echo "$BOT_PROCESSES" | xargs kill -KILL 2>/dev/null || true
    echo "✅ Instâncias anteriores paradas."
else
    echo "✅ Nenhuma instância do bot encontrada."
fi

# Ativar ambiente virtual
echo "🐍 Ativando ambiente virtual..."
source venv/bin/activate

# Executar o bot a partir do diretório src
echo "🚀 Iniciando bot..."
cd src && python main.py