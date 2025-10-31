# Configuração da SquareCloud para Bot VIP Telegram
# https://docs.squarecloud.app/pt-br/getting-started/config-file

# Nome de exibição da aplicação
DISPLAY_NAME=Bot VIP Telegram

# Descrição da aplicação
DESCRIPTION=Bot Telegram para gerenciamento de grupos VIP com sistema de pagamentos PIX e controle de assinaturas

# Arquivo principal da aplicação
MAIN=src/main.py

# Comando de inicialização
START=./start.sh

# Versão da aplicação
VERSION=latest

# Ambiente de execução (python)
ENVIRONMENT=python

# RAM necessária (em MB)
MEMORY=512

# Porta da aplicação (opcional, mas recomendado para Square Cloud)
PORT=8080

# Configuração para webhook (recomendado para Square Cloud)
WEBHOOK_URL=https://your-app-id.squarecloud.app

# Arquivos a incluir no deploy
# INCLUDE=.env.deploy

# Subdomínio personalizado (opcional)
# SUBDOMAIN=meu-bot

# Variáveis de ambiente (podem ser configuradas no painel também)
ENV_VARS=
  TELEGRAM_TOKEN="7729659551:AAEFWjED5bU4nCqgwhYpQa4UwvAK99WZ5vA"
  PIXGO_API_KEY="pk_7e5617a42e9b704d5e320629da68e0097edb718510cf01b3abb6b11bd33d92d9"
  PIXGO_BASE_URL="https://pixgo.org/api/v1"
  USDT_WALLET_ADDRESS="0x87C3373E83CDe3640F7b636033D2591ac05b4793"
  DATABASE_URL="sqlite:///botclient.db"
  SUBSCRIPTION_PRICE="10.0"
  SUBSCRIPTION_DAYS="30"
  LOG_LEVEL="INFO"
  LOG_FILE="logs/bot.log"
  ENVIRONMENT="production"