# Bot Telegram para Gestão de Grupos VIPs

Bot Telegram que gerencia grupos VIP com controle de acesso baseado em assinaturas via PIX (usando API PixGo) e suporte a USDT Polygon.

## Funcionalidades

### Comandos de Usuário
- `/pay` - Iniciar pagamento da assinatura via PIX
- `/status` - Ver status da assinatura
- `/renew` - Renovar assinatura
- `/help` - Mostrar comandos disponíveis
- `/invite` - Gerar link de convite

### Comandos de Admin
- `/add @usuario` - Adicionar usuário manualmente
- `/kick @usuario` - Remover usuário do grupo
- `/ban @usuario` - Banir usuário permanentemente
- `/mute @usuario` - Silenciar usuário temporariamente
- `/check @usuario` - Verificar status de pagamento
- `/broadcast mensagem` - Enviar mensagem para todos os membros

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual: `python3 -m venv venv`
3. Ative o ambiente: `source venv/bin/activate`
4. Instale as dependências: `pip install -e .`
5. Configure as variáveis de ambiente (veja `.env.example`)
6. Execute o bot: `./run_bot.sh` ou `python src/main.py`

## Configuração

Copie `.env.example` para `.env` e configure:

- `TELEGRAM_TOKEN` - Token do bot Telegram
- `PIXGO_API_KEY` - Chave da API PixGo
- `USDT_WALLET_ADDRESS` - Endereço da carteira USDT Polygon
- Outras configurações conforme necessário

## Desenvolvimento

- Formatação: `ruff format .`
- Linting: `ruff check .`
- Testes: `pytest`

## Arquitetura

- **Models**: SQLAlchemy models para User, Payment, Group, Admin
- **Services**: PixGo, USDT, Telegram integrations
- **Handlers**: Command handlers para user e admin
- **Utils**: Configuração e logging

## Banco de Dados

Por padrão usa SQLite. Para produção, configure PostgreSQL via `DATABASE_URL`.

## Licença

[Licença apropriada]