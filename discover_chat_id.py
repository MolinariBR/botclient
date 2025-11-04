#!/usr/bin/env python3
"""
Script para descobrir chat ID de um grupo Telegram
"""

import os
import sys
import requests
import base64

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

def decode_invite_link(invite_link):
    """Tenta decodificar o invite link para obter o chat ID"""
    # Links de grupo têm formato: https://t.me/+{invite_code}
    if '+ktTM6zv0UDYxYWY5' in invite_link:
        invite_code = 'ktTM6zv0UDYxYWY5'

        # Tentar diferentes métodos de decodificação
        try:
            # Método 1: Base64 decode
            decoded = base64.b64decode(invite_code + '==').decode('utf-8')
            print(f"🔍 Tentativa Base64: {decoded}")
        except:
            pass

        # Método 2: O invite code pode ser o chat ID codificado
        # Grupos têm IDs negativos, começando com -100
        # Vou tentar algumas possibilidades comuns

        print("🔍 Tentando descobrir chat ID do grupo...")
        print(f"📎 Invite Link: {invite_link}")
        print(f"🔑 Invite Code: {invite_code}")

        # Método 3: Usar API do Telegram para obter info do chat
        token = os.getenv('TELEGRAM_TOKEN')
        if token:
            # Tentar joinChatByInviteLink
            url = f"https://api.telegram.org/bot{token}/joinChatByInviteLink"
            data = {'invite_link': invite_link}

            try:
                response = requests.post(url, data=data, timeout=10)
                print(f"📡 Join response: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Join result: {data}")

                    if data.get('ok'):
                        chat = data.get('result', {})
                        chat_id = chat.get('id')
                        print(f"🎯 CHAT ID ENCONTRADO: {chat_id}")
                        return chat_id
                    else:
                        error = data.get('description', 'Unknown error')
                        print(f"❌ Join failed: {error}")
                else:
                    print(f"❌ HTTP Error: {response.status_code}")

            except Exception as e:
                print(f"❌ Error joining chat: {e}")

        # Método 4: Tentar getChat com possíveis IDs
        possible_ids = [
            -1000000000000,  # Placeholder para cálculos
            # Adicionar mais possibilidades se necessário
        ]

        print("🔍 Tentando IDs comuns de grupos...")
        for chat_id in possible_ids:
            try:
                url = f"https://api.telegram.org/bot{token}/getChat"
                data = {'chat_id': chat_id}
                response = requests.post(url, data=data, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        chat = data.get('result', {})
                        if 'title' in chat:
                            print(f"🎯 Possível match - ID: {chat_id}, Title: {chat.get('title')}")
                            return chat_id
            except:
                continue

    return None

def main():
    print("🔍 DESCOBRINDO CHAT ID DO GRUPO")
    print("=" * 40)

    load_env()

    invite_link = "https://t.me/+ktTM6zv0UDYxYWY5"
    print(f"🎯 Analisando: {invite_link}")

    chat_id = decode_invite_link(invite_link)

    if chat_id:
        print(f"\n🎉 CHAT ID ENCONTRADO: {chat_id}")
        print("💡 Configure no .env.local:")
        print(f"   TEST_CHAT_ID=\"{chat_id}\"")
    else:
        print("\n❌ Não foi possível descobrir o chat ID automaticamente.")
        print("🔧 SOLUÇÃO MANUAL:")
        print("1. Adicione @botria_bot ao grupo como administrador")
        print("2. Envie uma mensagem no grupo (ex: /start)")
        print("3. Execute: python get_chat_ids.py")
        print("4. Configure o TEST_CHAT_ID que aparecer")

    return 0

if __name__ == "__main__":
    sys.exit(main())