# Quickstart: Bot Telegram para Gestão de Grupos VIPs

## Pré-requisitos

- Python 3.11
- PostgreSQL
- Token do Telegram Bot
- API Key PixGo
- Endereço USDT Polygon

## Instalação

1. Clone o repositório e checkout para branch feature:
   ```bash
   git checkout 001-telegram-vip-groups-bot
   ```

2. Instale dependências:
   ```bash
   pip install python-telegram-bot requests sqlalchemy psycopg2
   ```

3. Configure variáveis de ambiente:
   ```bash
   export TELEGRAM_TOKEN="7729659551:AAEFWjED5bU4nCqgwhYpQaUwvAK99WZ5vA"
   export PIXGO_API_KEY="k_7e5617a42e9b704d5e320629da68e0097edb718510cf01b3abb6b11bd33d92d9"
   export USDT_ADDRESS="0x87C3373E83CDe3640F7b636033D2591ac05b4793"
   export DATABASE_URL="postgresql://user:pass@localhost/botdb"
   ```

4. Execute migrações do banco:
   ```bash
   python -c "from src.models import create_tables; create_tables()"
   ```

5. Inicie o bot:
   ```bash
   python src/main.py
   ```

## Teste Básico

1. Envie /start no chat direto com o bot.
2. Execute /pay para gerar QR PIX.
3. Como admin, execute /add @usuario para adicionar membro.
4. Execute /help para ver todos os comandos disponíveis.
5. Execute /status para ver status da assinatura.
6. Como admin, execute /kick @usuario para remover membro.
7. Como admin, execute /broadcast "Mensagem de teste" para enviar a todos.

## Testes Automatizados

Execute os testes automatizados para validar a implementação:

```bash
# Execute todos os testes
pytest tests/

# Execute apenas testes unitários
pytest tests/unit/

# Execute apenas testes de integração
pytest tests/integration/

# Execute apenas testes de contrato
pytest tests/contract/

# Com cobertura
pytest --cov=src --cov-report=html tests/
```

### Estrutura de Testes

- `tests/unit/`: Testes unitários para funções individuais
- `tests/integration/`: Testes de integração entre componentes
- `tests/contract/`: Testes baseados nos contratos da API PixGo

## Desenvolvimento

- Código em `src/`
- Testes em `tests/`
- Documentação em `specs/`
- Handlers para admins em `src/handlers/admin_handlers.py`
- Handlers para usuários em `src/handlers/user_handlers.py`

Para mais detalhes, consulte spec.md e plan.md.