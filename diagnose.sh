#!/bin/bash
# Script de diagnóstico para testar conectividade do bot

echo "=== DIAGNÓSTICO DO BOT TELEGRAM ==="
echo ""

# Verificar se as variáveis de ambiente estão configuradas
echo "1. Verificando variáveis de ambiente:"
echo "   TELEGRAM_TOKEN: ${TELEGRAM_TOKEN:0:20}..."
echo "   PIXGO_API_KEY: ${PIXGO_API_KEY:0:10}..."
echo "   PIXGO_BASE_URL: $PIXGO_BASE_URL"
echo "   DATABASE_URL: $DATABASE_URL"
echo "   USDT_WALLET_ADDRESS: ${USDT_WALLET_ADDRESS:0:10}..."
echo ""

# Verificar se as variáveis críticas estão definidas
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "   ❌ TELEGRAM_TOKEN não está definido!"
else
    echo "   ✅ TELEGRAM_TOKEN definido"
fi

if [ -z "$PIXGO_API_KEY" ]; then
    echo "   ❌ PIXGO_API_KEY não está definido!"
else
    echo "   ✅ PIXGO_API_KEY definido"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "   ❌ DATABASE_URL não está definido!"
else
    echo "   ✅ DATABASE_URL definido"
fi
echo ""
echo "2. Testando conectividade com Telegram API:"
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "   ❌ Não é possível testar - TELEGRAM_TOKEN não definido"
else
    if command -v curl &> /dev/null; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe" 2>/dev/null)
        if [ "$response" = "200" ]; then
            echo "   ✅ Conectividade OK (HTTP $response)"
        else
            echo "   ❌ Erro de conectividade (HTTP $response) - Token pode estar inválido"
        fi
    else
        echo "   ⚠️ curl não disponível para teste"
    fi
fi
echo ""

# Testar conectividade com PixGo API
echo "3. Testando conectividade com PixGo API:"
if [ -z "$PIXGO_BASE_URL" ]; then
    echo "   ❌ Não é possível testar - PIXGO_BASE_URL não definido"
elif [ -z "$PIXGO_API_KEY" ]; then
    echo "   ❌ Não é possível testar - PIXGO_API_KEY não definido"
else
    if command -v curl &> /dev/null; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "${PIXGO_BASE_URL}/health" 2>/dev/null)
        if [ "$response" = "200" ] || [ "$response" = "404" ]; then
            echo "   ✅ API PixGo acessível (HTTP $response)"
        else
            echo "   ❌ Erro na API PixGo (HTTP $response) - Verificar URL ou conectividade"
        fi
    else
        echo "   ⚠️ curl não disponível para teste"
    fi
fi
echo ""

# Verificar se o banco de dados pode ser criado
echo "4. Testando criação do banco de dados:"
python3 -c "
import os
import sqlite3
try:
    db_path = os.getenv('DATABASE_URL', 'sqlite:///botclient.db').replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    conn.execute('SELECT 1')
    conn.close()
    print('   ✅ Banco de dados OK')
except Exception as e:
    print(f'   ❌ Erro no banco: {e}')
"
echo ""

echo "=== DIAGNÓSTICO CONCLUÍDO ==="