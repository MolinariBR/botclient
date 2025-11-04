#!/usr/bin/env python3
"""
Script para verificar chats onde o bot é administrador
"""

import os
import sys
import requests

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

def get_bot_chats():
    """Obtém lista de chats onde o bot está"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN não encontrado")
        return []

    print("🔍 Verificando chats onde o bot está presente...")

    # Método 1: getUpdates para ver mensagens recentes
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                chats = []

                for update in updates:
                    message = update.get('message', {})
                    chat = message.get('chat', {})

                    chat_id = chat.get('id')
                    if chat_id and chat_id not in [c['id'] for c in chats]:
                        chats.append({
                            'id': chat_id,
                            'type': chat.get('type'),
                            'title': chat.get('title', 'N/A'),
                            'username': chat.get('username', 'N/A')
                        })

                if chats:
                    print("📨 Chats encontrados via updates:")
                    for chat in chats:
                        print(f"  📝 ID: {chat['id']} | Tipo: {chat['type']} | Título: {chat['title']}")
                else:
                    print("📭 Nenhum chat encontrado via updates")

                return chats
            else:
                print(f"❌ Erro na API: {data}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao obter updates: {e}")

    return []

def check_specific_group():
    """Verifica se conseguimos obter info do grupo específico"""
    token = os.getenv('TELEGRAM_TOKEN')
    invite_link = "https://t.me/+ktTM6zv0UDYxYWY5"

    print(f"\n🔍 Verificando grupo específico: {invite_link}")

    # Tentar obter info do chat usando o invite link
    url = f"https://api.telegram.org/bot{token}/getChat"
    data = {'chat_id': invite_link}

    try:
        response = requests.post(url, data=data, timeout=10)
        print(f"📡 getChat response: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                chat = data.get('result', {})
                chat_id = chat.get('id')
                print(f"✅ Grupo encontrado!")
                print(f"   📝 Chat ID: {chat_id}")
                print(f"   📋 Título: {chat.get('title', 'N/A')}")
                print(f"   👥 Tipo: {chat.get('type', 'N/A')}")
                return chat_id
            else:
                error = data.get('description', 'Unknown error')
                print(f"❌ Erro: {error}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Erro: {e}")

    return None

def main():
    print("🔍 VERIFICANDO CHATS DO BOT")
    print("=" * 40)

    load_env()

    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ Configure TELEGRAM_TOKEN no .env.local primeiro")
        return 1

    print(f"🤖 Bot: @{token.split(':')[0]}")

    # Verificar chats via updates
    chats = get_bot_chats()

    # Verificar grupo específico
    specific_chat_id = check_specific_group()

    if specific_chat_id:
        print(f"\n🎉 CHAT ID DO GRUPO ENCONTRADO: {specific_chat_id}")
        print("💡 Configure no .env.local:")
        print(f"   TEST_CHAT_ID=\"{specific_chat_id}\"")
        return 0

    if chats:
        print(f"\n📋 Chats encontrados: {len(chats)}")
        print("💡 Se o grupo estiver na lista acima, use o ID correspondente")
    else:
        print("\n❌ Nenhum chat encontrado")
        print("🔧 POSSÍVEIS SOLUÇÕES:")
        print("1. Certifique-se que @botria_bot está REALMENTE no grupo")
        print("2. Verifique se o bot tem permissões de admin")
        print("3. Envie uma mensagem no grupo (ex: /start)")
        print("4. Aguarde alguns minutos e execute novamente")

    return 0

if __name__ == "__main__":
    sys.exit(main())