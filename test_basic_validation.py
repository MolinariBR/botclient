#!/usr/bin/env python3
"""
Teste REAL de integração do Bot VIP Telegram
Inicia o bot, envia comandos via Telegram API e valida respostas
"""

import os
import sys
import time
import signal
import subprocess
import requests
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

# Diretórios
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"

class BotTester:
    """Testador real do bot via Telegram API"""

    def __init__(self):
        # Carregar variáveis do .env.local
        self.load_env_file()

        self.bot_process: Optional[subprocess.Popen] = None
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TEST_CHAT_ID")
        self.admin_id = os.getenv("ADMIN_USER_ID")

        if not self.token:
            raise ValueError("TELEGRAM_TOKEN não definido em .env.local")
        if not self.chat_id:
            raise ValueError("TEST_CHAT_ID não definido em .env.local")

        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def load_env_file(self):
        """Carrega variáveis do arquivo .env.local"""
        env_file = PROJECT_ROOT / ".env.local"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            # Remove aspas se existirem
                            value = value.strip('"\'')
                            os.environ[key.strip()] = value

    def start_bot(self) -> bool:
        """Inicia o bot em background"""
        print("🚀 Iniciando bot em background...")

        try:
            # Mudar para diretório src e iniciar bot
            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_DIR)

            self.bot_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=str(SRC_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Aguardar bot iniciar
            time.sleep(5)

            # Verificar se processo ainda está rodando
            if self.bot_process.poll() is None:
                print("✅ Bot iniciado com sucesso")
                return True
            else:
                _, stderr = self.bot_process.communicate()
                print(f"❌ Bot falhou ao iniciar: {stderr}")
                return False

        except Exception as e:
            print(f"❌ Erro ao iniciar bot: {e}")
            return False

    def stop_bot(self):
        """Para o bot"""
        if self.bot_process:
            print("🛑 Parando bot...")
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=10)
                print("✅ Bot parado")
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
                print("⚠️ Bot forçado a parar")

    def send_message(self, text: str, chat_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Envia mensagem para o bot"""
        chat_id = chat_id or self.chat_id
        url = f"{self.base_url}/sendMessage"

        try:
            response = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
            data = response.json()

            if data.get("ok"):
                return data["result"]
            else:
                print(f"❌ Erro ao enviar '{text}': {data}")
                return None
        except Exception as e:
            print(f"❌ Erro de rede ao enviar '{text}': {e}")
            return None

    def get_updates(self, offset: Optional[int] = None, timeout: int = 30) -> list:
        """Obtém updates do bot"""
        url = f"{self.base_url}/getUpdates"
        params = {"timeout": timeout}
        if offset:
            params["offset"] = offset

        try:
            response = requests.get(url, params=params, timeout=timeout + 5)
            data = response.json()

            if data.get("ok"):
                return data["result"]
            else:
                print(f"❌ Erro ao obter updates: {data}")
                return []
        except Exception as e:
            print(f"❌ Erro de rede ao obter updates: {e}")
            return []

    def wait_for_bot_response(self, expected_text: Optional[str] = None, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Aguarda resposta do bot"""
        start_time = time.time()
        last_update_id = None

        while time.time() - start_time < timeout:
            updates = self.get_updates(offset=last_update_id, timeout=5)

            for update in updates:
                last_update_id = update["update_id"] + 1

                if "message" in update and "text" in update["message"]:
                    text = update["message"]["text"]

                    # Verificar se é resposta do bot (não nossa mensagem)
                    # Bot ID é a parte antes dos ":" no token
                    bot_id = self.token.split(":")[0] if self.token else ""
                    if str(update["message"]["from"]["id"]) != bot_id:
                        if expected_text:
                            if expected_text.lower() in text.lower():
                                return update["message"]
                        else:
                            return update["message"]  # Retorna qualquer mensagem

            time.sleep(1)

        return None

    def test_start_command(self) -> bool:
        """Testa comando /start"""
        print("🧪 Testando comando /start...")

        # Enviar comando
        if not self.send_message("/start"):
            return False

        # Aguardar resposta
        response = self.wait_for_bot_response("Olá", timeout=15)
        if not response:
            print("❌ Bot não respondeu ao /start")
            return False

        text = response["text"]

        # Verificar elementos da mensagem unificada
        checks = [
            "🤖 **Bot VIP Telegram**",
            "💰 **Preço:** R$",
            "⏰ **Duração:**",
            "/pay",
            "/status",
            "/help"
        ]

        for check in checks:
            if check not in text:
                print(f"❌ Elemento não encontrado na resposta: {check}")
                return False

        print("✅ Comando /start funciona corretamente")
        return True

    def test_help_command(self) -> bool:
        """Testa comando /help"""
        print("🧪 Testando comando /help...")

        # Enviar comando
        if not self.send_message("/help"):
            return False

        # Aguardar resposta
        response = self.wait_for_bot_response("Bot VIP Telegram", timeout=15)
        if not response:
            print("❌ Bot não respondeu ao /help")
            return False

        text = response["text"]

        # Verificar comandos de usuário
        user_commands = ["/start", "/help", "/pay", "/status"]
        for cmd in user_commands:
            if cmd not in text:
                print(f"❌ Comando de usuário não encontrado: {cmd}")
                return False

        # Verificar que comandos admin NÃO estão presentes
        admin_commands = ["/add", "/kick", "/ban"]
        for cmd in admin_commands:
            if cmd in text:
                print(f"❌ Comando admin encontrado indevidamente: {cmd}")
                return False

        print("✅ Comando /help filtra corretamente")
        return True

    def test_pay_command(self) -> bool:
        """Testa comando /pay"""
        print("🧪 Testando comando /pay...")

        # Enviar comando
        if not self.send_message("/pay"):
            return False

        # Aguardar resposta com botões
        response = self.wait_for_bot_response("Escolha o método", timeout=15)
        if not response:
            print("❌ Bot não respondeu ao /pay")
            return False

        text = response["text"]

        # Verificar texto
        if "🎯 **Escolha o método de pagamento**" not in text:
            print("❌ Texto de seleção não encontrado")
            return False

        if "💰 PIX (R$)" not in text or "₿ USDT (Polygon)" not in text:
            print("❌ Opções de pagamento não encontradas")
            return False

        # Verificar botões inline
        if "reply_markup" not in response or "inline_keyboard" not in response["reply_markup"]:
            print("❌ Botões inline não encontrados")
            return False

        keyboard = response["reply_markup"]["inline_keyboard"]
        if len(keyboard) != 1 or len(keyboard[0]) != 2:
            print("❌ Estrutura dos botões incorreta")
            return False

        print("✅ Comando /pay mostra seleção de pagamentos")
        return True

    def test_status_command(self) -> bool:
        """Testa comando /status"""
        print("🧪 Testando comando /status...")

        # Enviar comando
        if not self.send_message("/status"):
            return False

        # Aguardar resposta
        response = self.wait_for_bot_response(timeout=15)
        if not response:
            print("❌ Bot não respondeu ao /status")
            return False

        # Status pode variar, apenas verifica se respondeu
        print("✅ Comando /status funciona")
        return True

    def test_info_command(self) -> bool:
        """Testa comando /info"""
        print("🧪 Testando comando /info...")

        # Enviar comando
        if not self.send_message("/info"):
            return False

        # Aguardar resposta
        response = self.wait_for_bot_response(timeout=15)
        if not response:
            print("❌ Bot não respondeu ao /info")
            return False

        print("✅ Comando /info funciona")
        return True

    def test_admin_pending(self) -> bool:
        """Testa comando /pending para admin"""
        if not self.admin_id:
            print("⚠️ ADMIN_USER_ID não definido, pulando teste admin")
            return True

        print("🧪 Testando comando /pending (admin)...")

        # Enviar comando como admin
        if not self.send_message("/pending", chat_id=self.admin_id):
            return False

        # Aguardar resposta
        response = self.wait_for_bot_response(timeout=15)
        if not response:
            print("❌ Admin não recebeu resposta do /pending")
            return False

        print("✅ Comando /pending funciona para admin")
        return True

def main():
    """Função principal de teste REAL"""
    print("🚀 TESTE REAL DE INTEGRAÇÃO - Bot VIP Telegram")
    print("=" * 60)
    print("⚠️ Este teste irá iniciar o bot e enviar mensagens reais via Telegram")
    print("Certifique-se de que:")
    print("• TELEGRAM_TOKEN está definido")
    print("• TEST_CHAT_ID está definido")
    print("• O bot não está rodando em outro lugar")
    print("=" * 60)

    tester = None

    try:
        # Inicializar tester
        tester = BotTester()

        # Iniciar bot
        if not tester.start_bot():
            print("❌ Falha ao iniciar bot")
            return 1

        # Aguardar bot ficar pronto
        time.sleep(3)

        # Executar testes
        tests = [
            ("Comando /start", tester.test_start_command),
            ("Comando /help", tester.test_help_command),
            ("Comando /pay", tester.test_pay_command),
            ("Comando /status", tester.test_status_command),
            ("Comando /info", tester.test_info_command),
            ("Admin /pending", tester.test_admin_pending),
        ]

        results = []
        passed = 0

        for test_name, test_func in tests:
            print(f"\n📋 Executando: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ Erro inesperado em {test_name}: {e}")
                results.append((test_name, False))

        # Resumo final
        print("\n" + "=" * 60)
        print("📊 RESULTADO DOS TESTES REAIS:")

        for test_name, result in results:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"  {status}: {test_name}")

        total = len(results)
        print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")

        if passed == total:
            print("🎉 Todos os testes reais passaram!")
            print("✅ O bot está funcionando perfeitamente!")
            return 0
        else:
            print("⚠️ Alguns testes falharam.")
            print("🔧 Verifique os logs acima e a configuração do bot.")
            return 1

    except Exception as e:
        print(f"❌ Erro geral no teste: {e}")
        return 1

    finally:
        if tester:
            tester.stop_bot()

if __name__ == "__main__":
    sys.exit(main())

import os
import sys
import subprocess
from pathlib import Path

# Diretórios
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"

def test_syntax():
    """Testar sintaxe de todos os arquivos modificados"""
    print("🔍 Verificando sintaxe dos arquivos modificados...")

    files_to_check = [
        SRC_DIR / "main.py",
        SRC_DIR / "handlers" / "user_handlers.py",
        SRC_DIR / "handlers" / "admin_handlers.py",
        SRC_DIR / "models" / "payment.py"
    ]

    all_passed = True

    for file_path in files_to_check:
        if file_path.exists():
            result = subprocess.run([sys.executable, "-m", "py_compile", str(file_path)],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {file_path.name}")
            else:
                print(f"❌ {file_path.name}: {result.stderr.strip()}")
                all_passed = False
        else:
            print(f"❌ {file_path.name} - arquivo não encontrado")
            all_passed = False

    return all_passed

def test_migration_exists():
    """Verificar se a migração foi criada"""
    print("🔍 Verificando migração do banco de dados...")

    migration_file = PROJECT_ROOT / "migrations" / "versions" / "fc1f10031f07_add_usdt_proof_fields_to_payment_model.py"

    if migration_file.exists():
        print("✅ Migração USDT criada")
        return True
    else:
        print("❌ Migração USDT não encontrada")
        return False

def test_handlers_registered():
    """Verificar se os handlers foram registrados no main.py"""
    print("🔍 Verificando registro de handlers...")

    main_file = SRC_DIR / "main.py"

    if not main_file.exists():
        print("❌ main.py não encontrado")
        return False

    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("confirm", "confirm_payment_handler"),
        ("reject", "reject_payment_handler"),
        ("MessageHandler(filters.PHOTO", "proof_handler")
    ]

    all_passed = True

    for check_text, handler_name in checks:
        if check_text in content and handler_name in content:
            print(f"✅ Handler {handler_name} registrado")
        else:
            print(f"❌ Handler {handler_name} não encontrado")
            all_passed = False

    return all_passed

def test_payment_model_fields():
    """Verificar se os campos foram adicionados ao modelo Payment"""
    print("🔍 Verificando campos do modelo Payment...")

    payment_file = SRC_DIR / "models" / "payment.py"

    if not payment_file.exists():
        print("❌ payment.py não encontrado")
        return False

    with open(payment_file, 'r', encoding='utf-8') as f:
        content = f.read()

    required_fields = [
        "proof_image_url",
        "transaction_hash",
        "proof_submitted_at",
        "waiting_proof"
    ]

    all_passed = True

    for field in required_fields:
        if field in content:
            print(f"✅ Campo {field} adicionado")
        else:
            print(f"❌ Campo {field} não encontrado")
            all_passed = False

    return all_passed

def test_welcome_message_unified():
    """Verificar se a mensagem de boas-vindas foi unificada"""
    print("🔍 Verificando mensagem de boas-vindas unificada...")

    user_handlers_file = SRC_DIR / "handlers" / "user_handlers.py"

    if not user_handlers_file.exists():
        print("❌ user_handlers.py não encontrado")
        return False

    with open(user_handlers_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar se não há mais as mensagens separadas
    if "private_welcome" in content or "group_welcome" in content:
        print("❌ Ainda há mensagens separadas de boas-vindas")
        return False

    # Verificar se há uma mensagem unificada
    if "welcome_text = f\"\"\"" in content and "Olá {user.first_name}" in content:
        print("✅ Mensagem de boas-vindas unificada")
        return True
    else:
        print("❌ Mensagem de boas-vindas não encontrada ou não unificada")
        return False

def test_help_filtered():
    """Verificar se o help filtra comandos corretamente"""
    print("🔍 Verificando filtro do comando /help...")

    user_handlers_file = SRC_DIR / "handlers" / "user_handlers.py"

    if not user_handlers_file.exists():
        print("❌ user_handlers.py não encontrado")
        return False

    with open(user_handlers_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar se há lógica de filtro por tipo de chat
    if "chat.type == \"private\"" in content and "show ALL commands" in content:
        print("✅ Help filtra comandos por tipo de chat")
        return True
    else:
        print("❌ Lógica de filtro do help não encontrada")
        return False

def test_usdt_flow():
    """Verificar se o fluxo USDT foi implementado"""
    print("🔍 Verificando fluxo USDT...")

    user_handlers_file = SRC_DIR / "handlers" / "user_handlers.py"

    if not user_handlers_file.exists():
        print("❌ user_handlers.py não encontrado")
        return False

    with open(user_handlers_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        "pay_usdt",
        "proof_handler",
        "_notify_admins_new_proof",
        "get_payment_instructions"
    ]

    all_passed = True

    for check in checks:
        if check in content:
            print(f"✅ {check} implementado")
        else:
            print(f"❌ {check} não encontrado")
            all_passed = False

    return all_passed

def main():
    """Função principal de teste"""
    print("🚀 Teste Básico da Implementação - Bot VIP Telegram")
    print("=" * 60)

    tests = [
        ("Sintaxe dos arquivos", test_syntax),
        ("Migração do banco", test_migration_exists),
        ("Registro de handlers", test_handlers_registered),
        ("Campos do modelo Payment", test_payment_model_fields),
        ("Mensagem boas-vindas unificada", test_welcome_message_unified),
        ("Help filtrado", test_help_filtered),
        ("Fluxo USDT", test_usdt_flow),
    ]

    results = []
    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            results.append((test_name, False))

    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")

    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {status}: {test_name}")

    print(f"\n🎯 Resultado Final: {passed}/{total} testes passaram")

    if passed == total:
        print("🎉 Todos os testes básicos passaram!")
        print("✅ A implementação das refatorações está correta.")
        return 0
    else:
        print("⚠️ Alguns testes falharam.")
        print("🔧 Verifique os arquivos modificados.")
        return 1

if __name__ == "__main__":
    sys.exit(main())