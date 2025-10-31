import requests
import json

token = '8126134321:AAE_kyQocfwQCJug4Vj_WYSHyQIQOX1H6RA'
chat_username = '@z9utafzw'

url = f'https://api.telegram.org/bot{token}/getChat'
data = {'chat_id': chat_username}

print(f'Consultando ID do chat: {chat_username}')
response = requests.post(url, data=data)

print(f'Status Code: {response.status_code}')

if response.status_code == 200:
    result = response.json()
    print(f'API Response OK: {result.get("ok")}')

    if result.get('ok'):
        chat_info = result['result']
        print(f'✅ ID do grupo/canal: {chat_info["id"]}')
        print(f'📝 Título: {chat_info.get("title", "N/A")}')
        print(f'👥 Tipo: {chat_info.get("type", "N/A")}')
        print(f'📊 Membros: {chat_info.get("members_count", "N/A")}')
    else:
        print(f'❌ Erro da API: {result.get("description", "Erro desconhecido")}')
        print(f'Código do erro: {result.get("error_code", "N/A")}')
else:
    print(f'❌ Erro HTTP {response.status_code}')
    print(f'Response: {response.text}')