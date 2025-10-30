import os
import requests
from dotenv import load_dotenv

# Carrega variáveis do .env.local
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env.local'))

token = os.getenv('TELEGRAM_TOKEN')
if not token:
    print('TELEGRAM_TOKEN não encontrado!')
    exit(1)

url = f'https://api.telegram.org/bot{token}/getMe'
print(f'Testando conexão com: {url}')

try:
    resp = requests.get(url, timeout=10)
    data = resp.json()
    print('Resposta da API:', data)
    if data.get('ok'):
        print('✅ Token válido e conexão com a API do Telegram funcionando!')
    else:
        print('❌ Token inválido ou problema na API:', data)
except Exception as e:
    print('❌ Erro ao conectar na API do Telegram:', e)
