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
VERSION=1.0.0

# Ambiente de execução (python)
ENVIRONMENT=python

# RAM necessária (em MB)
MEMORY=512

# Porta da aplicação (opcional - para aplicações web)
# PORT=8080

# Subdomínio personalizado (opcional)
# SUBDOMAIN=meu-bot

# Variáveis de ambiente (podem ser configuradas no painel também)
# ENV_VARS=
# TELEGRAM_TOKEN=seu_token_aqui
# PIXGO_API_KEY=sua_api_key_aqui
# PIXGO_BASE_URL=https://pixgo.org/api/v1
# USDT_WALLET_ADDRESS=seu_endereco_usdt
# DATABASE_URL=sqlite:///botclient.db
# SUBSCRIPTION_PRICE=50.0
# SUBSCRIPTION_DAYS=30
# LOG_LEVEL=INFO
# LOG_FILE=logs/bot.log