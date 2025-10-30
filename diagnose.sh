#!/bin/bash
# Script de diagnóstico para testar conectividade do bot

echo "=== DIAGNÓSTICO DO BOT TELEGRAM ==="
echo ""

# Verificar se as variáveis de ambiente estão configuradas
echo "1. Verificando variáveis de ambiente:"
echo "   TELEGRAM_TOKEN: ${TELEGRAM_TOKEN:0:20}..."
echo "   PIXGO_API_KEY: ${PIXGO_API_KEY:0:10}..."
echo "   DATABASE_URL: $DATABASE_URL"
echo ""

# Testar conectividade com Telegram API
echo "2. Testando conectividade com Telegram API:"
if command -v curl &> /dev/null; then
    response=$(curl -s -o /dev/null -w "%{http_code}" "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe" 2>/dev/null)
    if [ "$response" = "200" ]; then
        echo "   ✅ Conectividade OK (HTTP $response)"
    else
        echo "   ❌ Erro de conectividade (HTTP $response)"
    fi
else
    echo "   ⚠️ curl não disponível para teste"
fi
echo ""

# Testar conectividade com PixGo API
echo "3. Testando conectividade com PixGo API:"
if command -v curl &> /dev/null; then
    response=$(curl -s -o /dev/null -w "%{http_code}" "${PIXGO_BASE_URL}/health" 2>/dev/null)
    if [ "$response" = "200" ] || [ "$response" = "404" ]; then
        echo "   ✅ API PixGo acessível (HTTP $response)"
    else
        echo "   ❌ Erro na API PixGo (HTTP $response)"
    fi
else
    echo "   ⚠️ curl não disponível para teste"
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