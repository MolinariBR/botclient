import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

# Carrega variáveis do .env.local
load_dotenv('.env.local')

token = os.getenv('TELEGRAM_TOKEN')

async def start(update, context):
    await update.message.reply_text('Bot está funcionando!')

if not token:
    print('TELEGRAM_TOKEN não encontrado!')
    exit(1)

app = Application.builder().token(token).build()
app.add_handler(CommandHandler('start', start))

print('Bot mínimo rodando. Envie /start para o bot no Telegram.')
app.run_polling()
