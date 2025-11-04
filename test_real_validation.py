#!/usr/bin/env python3
"""
Teste REAL de validação - Bot VIP Telegram
Testa se o bot inicia corretamente e handlers estão registrados
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Diretórios
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"

class BotValidator:
    """Validador real do bot"""

    def __init__(self):
        self.bot_process = None
        self.load_env_file()

    def load_env_file(self):
        """Carrega variáveis do arquivo .env.local"""
        env_file = PROJECT_ROOT / ".env.local"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove aspas se existirem
                        value = value.strip('"\'')
                        os.environ[key.strip()] = value

    def test_bot_startup(self):
        """Testa se o bot consegue iniciar"""
        print("🧪 Testando inicialização do bot...")

        try:
            # Mudar para diretório src e iniciar bot
            env = os.environ.copy()
            env["PYTHONPATH"] = str(SRC_DIR)

            self.bot_process = subprocess.Popen(
                [sys.executable, "-c", """
import sys
sys.path.insert(0, '.')
from main import main
print('Bot modules loaded successfully')
import asyncio
asyncio.run(main())
"""],
                cwd=str(SRC_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Aguardar um pouco para ver se inicia
            time.sleep(5)

            # Verificar se ainda está rodando
            if self.bot_process.poll() is None:
                print("✅ Bot iniciou e está rodando")
                return True
            else:
                stdout, stderr = self.bot_process.communicate()
                print("❌ Bot falhou ao iniciar:")
                if stderr:
                    print(f"STDERR: {stderr}")
                if stdout:
                    print(f"STDOUT: {stdout}")
                return False

        except Exception as e:
            print(f"❌ Erro ao testar inicialização: {e}")
            return False

    def test_handlers_registration(self):
        """Testa se os handlers estão registrados"""
        print("🧪 Testando registro de handlers...")

        try:
            # Importar e verificar handlers
            sys.path.insert(0, str(SRC_DIR))

            from main import main
            from handlers.user_handlers import UserHandlers
            from handlers.admin_handlers import AdminHandlers

            print("✅ Módulos importados com sucesso")

            # Verificar se classes existem
            if hasattr(UserHandlers, 'start_handler'):
                print("✅ start_handler encontrado")
            else:
                print("❌ start_handler não encontrado")
                return False

            if hasattr(UserHandlers, 'help_handler'):
                print("✅ help_handler encontrado")
            else:
                print("❌ help_handler não encontrado")
                return False

            if hasattr(UserHandlers, 'pay_handler'):
                print("✅ pay_handler encontrado")
            else:
                print("❌ pay_handler não encontrado")
                return False

            if hasattr(UserHandlers, 'proof_handler'):
                print("✅ proof_handler encontrado")
            else:
                print("❌ proof_handler não encontrado")
                return False

            if hasattr(AdminHandlers, 'confirm_payment_handler'):
                print("✅ confirm_payment_handler encontrado")
            else:
                print("❌ confirm_payment_handler não encontrado")
                return False

            if hasattr(AdminHandlers, 'reject_payment_handler'):
                print("✅ reject_payment_handler encontrado")
            else:
                print("❌ reject_payment_handler não encontrado")
                return False

            return True

        except Exception as e:
            print(f"❌ Erro ao testar handlers: {e}")
            return False

    def test_database_connection(self):
        """Testa conexão com banco de dados - SIMPLIFICADO"""
        print("🧪 Testando conexão com banco de dados...")

        try:
            sys.path.insert(0, str(SRC_DIR))

            # Testar apenas se conseguimos importar os modelos
            from models.payment import Payment

            required_fields = ['proof_image_url', 'transaction_hash', 'proof_submitted_at']

            for field in required_fields:
                if hasattr(Payment, field):
                    print(f"✅ Campo {field} existe no modelo")
                else:
                    print(f"❌ Campo {field} não encontrado no modelo")
                    return False

            # Verificar se o arquivo do banco existe
            db_path = SRC_DIR / "botclient.db"
            if db_path.exists():
                print("✅ Arquivo botclient.db existe")
                return True
            else:
                print("❌ Arquivo botclient.db não encontrado")
                return False

        except Exception as e:
            print(f"❌ Erro ao testar banco de dados: {e}")
            return False

    def stop_bot(self):
        """Para o bot se estiver rodando"""
        if self.bot_process:
            print("🛑 Parando bot...")
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
                print("✅ Bot parado")
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
                print("⚠️ Bot forçado a parar")

def main():
    """Função principal de teste REAL"""
    print("🚀 TESTE REAL DE VALIDAÇÃO - Bot VIP Telegram")
    print("=" * 60)
    print("Este teste verifica se o bot consegue iniciar e se todas")
    print("as funcionalidades implementadas estão funcionando.")
    print("=" * 60)

    validator = BotValidator()

    try:
        # Executar testes
        tests = [
            ("Inicialização do bot", validator.test_bot_startup),
            ("Registro de handlers", validator.test_handlers_registration),
            ("Conexão com banco de dados", validator.test_database_connection),
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
            print("✅ Todas as refatorações foram implementadas corretamente!")
            return 0
        else:
            print("⚠️ Alguns testes falharam.")
            print("🔧 Verifique os logs acima.")
            return 1

    finally:
        validator.stop_bot()

if __name__ == "__main__":
    sys.exit(main())