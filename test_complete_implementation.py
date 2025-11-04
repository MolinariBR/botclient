#!/usr/bin/env python3
"""
Script de teste completo do Bot VIP Telegram
Testa todas as funcionalidades implementadas nas refatorações
"""

import os
import sys
import subprocess
import time
import signal
import requests
import json
from pathlib import Path

# Determinar o diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"

# Adicionar diretório src ao path
sys.path.insert(0, str(SRC_DIR))

def load_env():
    """Carregar variáveis de ambiente"""
    # Tentar múltiplos arquivos de configuração
    env_files = [
        PROJECT_ROOT / ".env.local",
        PROJECT_ROOT / ".env",
        SRC_DIR / ".env.local",
        SRC_DIR / ".env"
    ]

    for env_file in env_files:
        if env_file.exists():
            print(f"📄 Carregando variáveis de {env_file}")
            with open(env_file) as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        try:
                            key, value = line.strip().split('=', 1)
                            os.environ[key.strip()] = value.strip()
                        except ValueError:
                            pass  # Ignorar linhas mal formatadas
            break
    else:
        print("⚠️ Nenhum arquivo .env encontrado")

def check_bot_imports():
    """Verificar se todos os imports do bot funcionam"""
    print("🔍 Verificando imports do bot...")

    try:
        sys.path.insert(0, str(SRC_DIR))
        from main import main
        print("✅ main.py importa corretamente")
    except Exception as e:
        print(f"❌ Erro ao importar main.py: {e}")
        return False

    try:
        from handlers.user_handlers import UserHandlers
        print("✅ user_handlers.py importa corretamente")
    except Exception as e:
        print(f"❌ Erro ao importar user_handlers.py: {e}")
        return False

    try:
        from handlers.admin_handlers import AdminHandlers
        print("✅ admin_handlers.py importa corretamente")
    except Exception as e:
        print(f"❌ Erro ao importar admin_handlers.py: {e}")
        return False

    try:
        from models.payment import Payment
        print("✅ models/payment.py importa corretamente")
    except Exception as e:
        print(f"❌ Erro ao importar models/payment.py: {e}")
        return False

    return True

def check_database():
    """Verificar se o banco de dados tem as tabelas corretas"""
    print("🔍 Verificando banco de dados...")

    try:
        sys.path.insert(0, str(SRC_DIR))
        from sqlalchemy import create_engine, inspect
        from config import Config

        db_path = SRC_DIR / "botclient.db"
        if not db_path.exists():
            print("❌ Arquivo botclient.db não encontrado")
            return False

        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)

        required_tables = ['users', 'payments', 'admins', 'groups', 'group_memberships']
        existing_tables = inspector.get_table_names()

        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Tabela {table} existe")
            else:
                print(f"❌ Tabela {table} não encontrada")
                return False

        # Verificar colunas da tabela payments
        payment_columns = [col['name'] for col in inspector.get_columns('payments')]
        required_payment_cols = ['proof_image_url', 'transaction_hash', 'proof_submitted_at']

        for col in required_payment_cols:
            if col in payment_columns:
                print(f"✅ Coluna {col} existe na tabela payments")
            else:
                print(f"❌ Coluna {col} não encontrada na tabela payments")
                return False

        return True

    except Exception as e:
        print(f"❌ Erro ao verificar banco de dados: {e}")
        return False

def test_bot_syntax():
    """Testar sintaxe de todos os arquivos Python modificados"""
    print("🔍 Verificando sintaxe dos arquivos...")

    files_to_check = [
        SRC_DIR / "main.py",
        SRC_DIR / "handlers" / "user_handlers.py",
        SRC_DIR / "handlers" / "admin_handlers.py",
        SRC_DIR / "models" / "payment.py"
    ]

    for file_path in files_to_check:
        if file_path.exists():
            result = subprocess.run([sys.executable, "-m", "py_compile", str(file_path)],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Sintaxe de {file_path.name} está correta")
            else:
                print(f"❌ Erro de sintaxe em {file_path.name}: {result.stderr}")
                return False
        else:
            print(f"❌ Arquivo {file_path.name} não encontrado")
            return False

    return True

def test_telegram_connection():
    """Testar conexão com API do Telegram"""
    print("🔍 Testando conexão com Telegram...")

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("❌ TELEGRAM_TOKEN não definido")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("ok"):
            bot_info = data.get("result", {})
            print(f"✅ Conectado ao bot: @{bot_info.get('username', 'unknown')}")
            return True
        else:
            print(f"❌ Erro na API do Telegram: {data}")
            return False

    except Exception as e:
        print(f"❌ Erro ao conectar com Telegram: {e}")
        return False

def test_commands_via_api():
    """Testar comandos básicos via API do Telegram"""
    print("🔍 Testando comandos via API do Telegram...")

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TEST_CHAT_ID")

    if not token or not chat_id:
        print("❌ TELEGRAM_TOKEN ou TEST_CHAT_ID não definidos")
        return False

    base_url = f"https://api.telegram.org/bot{token}"

    # Lista de comandos para testar
    test_commands = [
        "/start",
        "/help",
        "/status"
    ]

    for cmd in test_commands:
        try:
            url = f"{base_url}/sendMessage"
            payload = {"chat_id": chat_id, "text": cmd}

            response = requests.post(url, data=payload, timeout=10)
            data = response.json()

            if data.get("ok"):
                print(f"✅ Comando {cmd} enviado com sucesso")
                time.sleep(1)  # Pequena pausa entre comandos
            else:
                print(f"❌ Falha ao enviar {cmd}: {data}")
                return False

        except Exception as e:
            print(f"❌ Erro ao testar comando {cmd}: {e}")
            return False

    return True

def run_unit_tests():
    """Executar testes unitários"""
    print("🔍 Executando testes unitários...")

    try:
        result = subprocess.run([sys.executable, "-m", "pytest", str(PROJECT_ROOT / "tests" / "unit"), "-v"],
                              capture_output=True, text=True, cwd=str(PROJECT_ROOT))

        if result.returncode == 0:
            print("✅ Todos os testes unitários passaram")
            return True
        else:
            print(f"❌ Alguns testes unitários falharam: {result.stdout}")
            return False

    except Exception as e:
        print(f"❌ Erro ao executar testes unitários: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes completos do Bot VIP Telegram")
    print("=" * 60)

    # Carregar variáveis de ambiente
    load_env()

    tests = [
        ("Verificação de imports", check_bot_imports),
        ("Sintaxe dos arquivos", test_bot_syntax),
        ("Banco de dados", check_database),
        ("Conexão Telegram", test_telegram_connection),
        ("Comandos via API", test_commands_via_api),
        ("Testes unitários", run_unit_tests),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Executando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))

    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 Todos os testes passaram! O bot está funcionando corretamente.")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())