#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()
import requests
import os

token = os.getenv('TELEGRAM_TOKEN')
if not token:
    print('❌ No token')
    exit(1)

print(f'Testing token: ***{token[-10:]}')

url = f'https://api.telegram.org/bot{token}/getMe'
try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot = data['result']
            print(f'✅ Bot: @{bot["username"]} (ID: {bot["id"]})')
            print(f'   Can join groups: {bot["can_join_groups"]}')
            print(f'   Can read messages: {bot["can_read_all_group_messages"]}')
        else:
            print(f'❌ API error: {data}')
    else:
        print(f'❌ HTTP {response.status_code}: {response.text[:100]}')
except Exception as e:
    print(f'❌ Error: {e}')