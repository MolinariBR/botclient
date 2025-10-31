import requests

# Dados do bot
token = '8126134321:AAE_kyQocfwQCJug4Vj_WYSHyQIQOX1H6RA'
chat_id = '1654650952'  # ID do admin criptodms

# Comando para registrar o grupo
command = '/register_group -1002916380502'

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = {
    'chat_id': chat_id,
    'text': command
}

print(f'Enviando comando: {command}')
print(f'Para chat ID: {chat_id}')

response = requests.post(url, data=data)

if response.status_code == 200:
    result = response.json()
    if result.get('ok'):
        print('✅ Comando enviado com sucesso!')
        print('Verifique seu chat privado com o bot para ver a resposta.')
    else:
        print(f'❌ Erro da API: {result.get("description")}')
else:
    print(f'❌ Erro HTTP {response.status_code}: {response.text}')