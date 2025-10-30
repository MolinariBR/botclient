#!/bin/bash
# Script para testar especificamente o token do Telegram

echo "=== TESTE DO TOKEN TELEGRAM ==="

if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "❌ ERRO: TELEGRAM_TOKEN não está definido!"
    exit 1
fi

echo "Token definido: ${TELEGRAM_TOKEN:0:20}..."
echo ""

echo "Testando API do Telegram..."
response=$(curl -s -w "HTTPSTATUS:%{http_code};" "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe" 2>/dev/null)

# Extrair o código HTTP
http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

# Extrair o corpo da resposta
body=$(echo $response | sed -e 's/HTTPSTATUS:.*//g')

echo "Código HTTP: $http_code"
echo "Resposta: $body"
echo ""

if [ "$http_code" = "200" ]; then
    echo "✅ Token válido!"
    # Extrair informações do bot
    bot_username=$(echo $body | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    bot_name=$(echo $body | grep -o '"first_name":"[^"]*"' | cut -d'"' -f4)
    echo "Nome do bot: $bot_name"
    echo "Username: @$bot_username"
else
    echo "❌ Token inválido ou erro na API"
    if [ "$http_code" = "404" ]; then
        echo "Erro 404: Token provavelmente incorreto"
    elif [ "$http_code" = "401" ]; then
        echo "Erro 401: Token inválido"
    else
        echo "Erro $http_code: Problema de conectividade"
    fi
fi

echo "=== FIM DO TESTE ==="