#!/usr/bin/env python3
"""
Script para verificar se o bot está realmente no grupo e tem permissões
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

def test_bot_membership():
    """Testa se o bot está no grupo e suas permissões"""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ TELEGRAM_TOKEN não encontrado")
        return

    # IDs de grupo comuns - vamos tentar alguns
    possible_group_ids = [
        "-1001234567890",  # Placeholder
        "-1000000000000",  # Outro placeholder
        # Adicionar mais se necessário
    ]

    print("🔍 Testando membership do bot em possíveis grupos...")

    bot_id = token.split(':')[0]

    for group_id in possible_group_ids:
        try:
            # Testar getChatMember
            url = f"https://api.telegram.org/bot{token}/getChatMember"
            data = {
                'chat_id': group_id,
                'user_id': bot_id
            }

            response = requests.post(url, data=data, timeout=10)
            print(f"📡 Testando grupo {group_id}: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    member = data.get('result', {})
                    status = member.get('status')
                    print(f"✅ Bot encontrado no grupo {group_id}!")
                    print(f"   📊 Status: {status}")
                    print(f"   👑 Admin: {member.get('can_manage_chat', False)}")
                    return group_id
                else:
                    error = data.get('description', '')
                    if 'chat not found' not in error.lower():
                        print(f"   ⚠️  Resposta: {error}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Erro: {e}")
            continue

    return None

def manual_chat_id_calculation():
    """Tenta calcular o chat ID baseado no invite code"""
    print("\n🔍 Tentando calcular chat ID do invite code...")

    invite_code = "ktTM6zv0UDYxYWY5"

    # Grupos do Telegram têm IDs negativos começando com -100
    # O invite code pode ser usado para calcular o ID

    # Método 1: Tentar conversão direta
    try:
        # Alguns grupos usam o invite code como parte do ID
        possible_id = f"-100{invite_code}"
        print(f"📝 Tentativa 1: {possible_id}")
        return possible_id
    except:
        pass

    # Método 2: Procurar por padrões conhecidos
    print("📝 Método alternativo: Use o link https://t.me/+ktTM6zv0UDYxYWY5")
    print("   1. Abra o link no navegador")
    print("   2. Adicione @botria_bot ao grupo")
    print("   3. Execute: python get_chat_ids.py")

    return None

def main():
    print("🔍 VERIFICANDO MEMBERSHIP DO BOT")
    print("=" * 40)

    load_env()

    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("❌ Configure TELEGRAM_TOKEN no .env.local primeiro")
        return 1

    print(f"🤖 Bot ID: {token.split(':')[0]}")
    print("🎯 Grupo alvo: https://t.me/+ktTM6zv0UDYxYWY5")

    # Testar membership
    found_group_id = test_bot_membership()

    if found_group_id:
        print(f"\n🎉 GRUPO ENCONTRADO! Chat ID: {found_group_id}")
        print("💡 Configure no .env.local:")
        print(f"   TEST_CHAT_ID=\"{found_group_id}\"")
        return 0

    # Método alternativo
    calc_id = manual_chat_id_calculation()

    if calc_id:
        print(f"\n💡 Chat ID calculado: {calc_id}")
        print("🧪 Teste este ID:")
        print(f"   TEST_CHAT_ID=\"{calc_id}\"")
        print("   Execute: python test_bot_messages.py")

    print("\n❌ Não foi possível determinar o chat ID automaticamente.")
    print("🔧 SOLUÇÃO DEFINITIVA:")
    print("1. Abra: https://t.me/+ktTM6zv0UDYxYWY5")
    print("2. CONFIRME que @botria_bot está na lista de admins")
    print("3. Envie: /start no grupo")
    print("4. Execute: python get_chat_ids.py")
    print("5. Use o ID que aparecer")

    return 0

if __name__ == "__main__":
    sys.exit(main())