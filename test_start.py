import requests

# Dados do bot
token = '8126134321:AAE_kyQocfwQCJug4Vj_WYSHyQIQOX1H6RA'
chat_id = '1654650952'  # ID do admin criptodms

# Comando simples para testar
command = '/start'

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = {
    'chat_id': chat_id,
    'text': command
}

print(f'Enviando comando: {command}')
response = requests.post(url, data=data)

if response.status_code == 200:
    result = response.json()
    if result.get('ok'):
        print('✅ Comando /start enviado com sucesso!')
    else:
        print(f'❌ Erro da API: {result.get("description")}')
else:
    print(f'❌ Erro HTTP {response.status_code}: {response.text}')