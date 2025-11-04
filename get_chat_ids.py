#!/usr/bin/env python3
"""
Script para obter chat IDs do bot
"""

import os
import sys
import requests
import time

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

def get_updates():
    """Obtém updates do bot para ver chat IDs"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN não encontrado")
        return

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                if not updates:
                    print("📭 Nenhuma mensagem recebida ainda.")
                    print("Envie uma mensagem para o bot ou adicione-o a um grupo!")
                    return

                print("📨 Últimas mensagens recebidas:")
                for update in updates[-5:]:  # Últimas 5
                    message = update.get('message', {})
                    chat = message.get('chat', {})
                    user = message.get('from', {})

                    chat_id = chat.get('id')
                    chat_type = chat.get('type')
                    chat_title = chat.get('title', 'N/A')
                    username = user.get('username', 'N/A')

                    print(f"  📝 Chat ID: {chat_id}")
                    print(f"     Tipo: {chat_type}")
                    print(f"     Título: {chat_title}")
                    print(f"     Usuário: @{username}")
                    print()

                # Sugerir configuração
                if updates:
                    last_chat = updates[-1].get('message', {}).get('chat', {})
                    suggested_id = last_chat.get('id')
                    print(f"💡 Configure TEST_CHAT_ID='{suggested_id}' no arquivo .env.local")

            else:
                print(f"❌ Erro na resposta: {data}")
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    print("🔍 OBTENDO CHAT IDs DO BOT")
    print("=" * 40)

    load_env()

    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ Configure TELEGRAM_TOKEN no .env.local primeiro")
        return 1

    print(f"🤖 Bot: @{token.split(':')[0]}")
    print("Aguardando mensagens... (envie uma mensagem para o bot)")

    # Aguardar um pouco
    time.sleep(2)

    get_updates()

    print("\n" + "=" * 40)
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Adicione o bot a um grupo OU envie mensagem privada")
    print("2. Execute este script novamente")
    print("3. Configure TEST_CHAT_ID no .env.local")
    print("4. Teste o bot com: python test_bot_messages.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())