#!/usr/bin/env python3
"""
Teste direto de envio de mensagens para o bot
"""

import os
import sys
import requests
import time

# Carregar configurações
def load_env():
    env_file = ".env.local"
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key.strip()] = value

def test_bot_connection():
    """Testa se conseguimos nos conectar ao bot via API"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN não encontrado")
        return False

    print(f"🔑 Token encontrado: {token[:10]}...")

    # Testar getMe
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ Bot conectado: @{bot_info.get('username')} (ID: {bot_info.get('id')})")
                return True
            else:
                print(f"❌ Erro na resposta: {data}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def test_send_message():
    """Testa envio de mensagem"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TEST_CHAT_ID') or os.getenv('ADMIN_USER_ID')

    if not chat_id:
        print("❌ TEST_CHAT_ID ou ADMIN_USER_ID não encontrado")
        return False

    print(f"📤 Testando envio para chat_id: {chat_id}")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': '🧪 *TESTE DO BOT VIP* 🧪\n\nEste é um teste automático para verificar se o bot está funcionando corretamente.',
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ Mensagem enviada com sucesso!")
                return True
            else:
                print(f"❌ Erro na resposta: {data}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return False

def main():
    print("🚀 TESTE DIRETO DE CONEXÃO COM BOT TELEGRAM")
    print("=" * 50)

    # Carregar configurações
    load_env()

    # Testar conexão
    if not test_bot_connection():
        print("❌ Falha na conexão com o bot")
        return 1

    # Testar envio de mensagem
    if not test_send_message():
        print("❌ Falha no envio de mensagem")
        return 1

    print("✅ Todos os testes passaram!")
    return 0

if __name__ == "__main__":
    sys.exit(main())