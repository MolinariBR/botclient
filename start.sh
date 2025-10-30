#!/bin/bash

# Script de inicialização para SquareCloud
# Este script é executado automaticamente pela SquareCloud

echo "🚀 Iniciando Bot VIP Telegram..."

# Verificar se estamos no ambiente correto
if [ -d "/home/container" ]; then
    cd /home/container
    echo "📁 Diretório de trabalho: /home/container"
else
    echo "📁 Diretório de trabalho: $(pwd)"
fi

# Configurar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Verificar se o Python está disponível
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python não encontrado!"
    exit 1
fi

echo "🐍 Usando Python: $($PYTHON_CMD --version)"

# Verificar se o arquivo main.py existe
if [ ! -f "src/main.py" ]; then
    echo "❌ Arquivo src/main.py não encontrado!"
    exit 1
fi

echo "✅ Arquivo main.py encontrado"

# Verificar variáveis de ambiente
echo "🔧 Verificando variáveis de ambiente..."
./check_env.sh

# Testar token do Telegram
echo "🤖 Testando token do Telegram..."
./test_token.sh

# Executar diagnóstico de conectividade
echo "🔍 Executando diagnóstico de conectividade..."
./diagnose.sh

# Executar o bot
echo "🤖 Executando o bot..."
exec $PYTHON_CMD src/main.py