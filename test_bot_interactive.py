#!/usr/bin/env python3
"""
Teste simples para verificar se o bot responde a comandos
"""

import os
import sys
import subprocess
import time
import signal

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

def test_bot_startup():
    """Inicia o bot e verifica se ele está funcionando"""
    print("🚀 Iniciando bot para teste...")

    load_env()

    try:
        # Iniciar bot em background
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"

        process = subprocess.Popen(
            [sys.executable, "-m", "src.main"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print("⏳ Aguardando bot inicializar...")
        time.sleep(10)  # Aguardar inicialização

        # Verificar se ainda está rodando
        if process.poll() is None:
            print("✅ Bot iniciado com sucesso!")
            print("📱 Agora teste os comandos no grupo:")
            print("   • /start")
            print("   • /help")
            print("   • /pay")
            print("")
            print("⏹️  Pressione Ctrl+C para parar o bot")

            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Parando bot...")
                process.terminate()
                process.wait(timeout=5)
                print("✅ Bot parado")

        else:
            stdout, stderr = process.communicate()
            print("❌ Bot falhou ao iniciar:")
            if stderr:
                print(f"STDERR: {stderr}")
            if stdout:
                print(f"STDOUT: {stdout}")

    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    print("🧪 TESTE DE FUNCIONAMENTO DO BOT")
    print("=" * 40)
    print("Este teste inicia o bot e permite testar comandos manualmente.")
    print("=" * 40)

    test_bot_startup()

    return 0

if __name__ == "__main__":
    sys.exit(main())