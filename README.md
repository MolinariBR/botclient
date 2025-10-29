# 🤖 Bot VIP Telegram - Gestão de Grupos Premium

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot_API-blue.svg)](https://core.telegram.org/bots/api)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-green.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Bot Telegram completo para gerenciamento de grupos VIP com sistema de assinaturas, controle de acesso baseado em pagamentos via PIX e USDT, moderação automática e painel administrativo completo.

## ✨ Funcionalidades Principais

### 💰 Sistema de Pagamentos
- **PIX Integrado**: Pagamentos via PixGo API com QR Code automático
- **USDT Polygon**: Suporte a pagamentos em criptomoedas
- **Assinaturas Automáticas**: Renovação automática opcional
- **Controle de Expiração**: Remoção automática de membros expirados

### 👥 Gerenciamento de Usuários
- **Controle de Acesso**: Apenas membros com assinatura ativa
- **Sistema de Avisos**: Warnings progressivos com auto-ban
- **Moderação**: Mute, kick e ban com comandos simples
- **Histórico Completo**: Logs de todas as ações

### 📊 Painel Administrativo
- **Dashboard Completo**: Estatísticas em tempo real
- **Gerenciamento de Grupos**: Múltiplos grupos por bot
- **Configurações Dinâmicas**: Preços e regras editáveis
- **Broadcast**: Mensagens para todos os membros

### 🔧 Recursos Avançados
- **Mensagens Agendadas**: Sistema de lembretes automáticos
- **Backup/Restore**: Exportação e importação de dados
- **Performance Monitoring**: Acompanhamento de uso de recursos
- **Logs Estruturados**: Sistema de logging completo

## 🚀 Instalação Rápida

### Pré-requisitos
- Python 3.11+
- Conta no [PixGo](https://pixgo.org) (para pagamentos PIX)
- Carteira USDT Polygon (opcional)
- Bot Telegram criado via [@BotFather](https://t.me/botfather)

### Passos de Instalação

1. **Clone o repositório**
   ```bash
   git clone <seu-repositorio>
   cd botclient
   ```

2. **Configure o ambiente virtual**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

3. **Instale as dependências**
   ```bash
   pip install -e .
   ```

4. **Configure as variáveis de ambiente**
   ```bash
   cp .env.example .env
   # Edite o .env com suas configurações
   ```

5. **Inicialize o banco de dados**
   ```bash
   python init_db.py
   ```

6. **Execute o bot**
   ```bash
   ./run_bot.sh
   ```

## ⚙️ Configuração Detalhada

### Variáveis de Ambiente (.env)

```bash
# Telegram Bot
TELEGRAM_TOKEN=seu_token_aqui

# Pagamentos PIX
PIXGO_API_KEY=sua_api_key_pixgo
PIXGO_BASE_URL=https://pixgo.org/api/v1

# Pagamentos USDT (opcional)
USDT_WALLET_ADDRESS=seu_endereco_usdt_polygon

# Banco de Dados
DATABASE_URL=sqlite:///botclient.db

# Configurações do Sistema
SUBSCRIPTION_PRICE=50.0
SUBSCRIPTION_DAYS=30
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
```

### Primeiro Admin

Após iniciar o bot, registre o primeiro administrador:

1. Envie `/add @seu_usuario` em uma conversa privada com o bot
2. Verifique com `/admins`

### Registro de Grupos

Para cada grupo VIP:
1. Adicione o bot como administrador no grupo
2. No grupo, envie `/register_group`
3. Configure preços e regras via comandos admin

## 📚 Como Usar

### Para Usuários

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/start` | Inicia o bot e mostra informações | `/start` |
| `/pay` | Inicia processo de pagamento | `/pay` |
| `/status` | Verifica status da assinatura | `/status` |
| `/renew` | Renova assinatura | `/renew` |
| `/cancel` | Cancela renovação automática | `/cancel` |
| `/help` | Mostra todos os comandos | `/help` |
| `/invite` | Gera link de convite | `/invite` |
| `/support` | Contato com administradores | `/support` |

### Para Administradores

#### Gerenciamento de Usuários
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/add @user` | Adiciona usuário VIP | `/add @johndoe` |
| `/kick @user` | Remove do grupo | `/kick @spammer` |
| `/ban @user` | Banimento permanente | `/ban @violador` |
| `/unban @user` | Remove banimento | `/unban @user` |
| `/mute @user [tempo]` | Silencia temporariamente | `/mute @user 1h` |
| `/unmute @user` | Remove silêncio | `/unmute @user` |
| `/warn @user [motivo]` | Aplica aviso | `/warn @user Spam` |
| `/resetwarn @user` | Zera avisos | `/resetwarn @user` |

#### Controle de Pagamentos
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/check @user` | Status de pagamento | `/check @user` |
| `/renew @user` | Renova manualmente | `/renew @user` |
| `/expire @user` | Expira acesso | `/expire @user` |
| `/pending` | Pagamentos pendentes | `/pending` |

#### Comunicação
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/broadcast [msg]` | Mensagem para todos | `/broadcast Manutenção hoje!` |
| `/schedule [hora] [msg]` | Agenda mensagem | `/schedule 15:00 Aula começa!` |
| `/sendto @user [msg]` | Mensagem privada | `/sendto @user Sua assinatura expira` |

#### Configurações
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/setprice [valor] [moeda]` | Define preço | `/setprice 89.90 BRL` |
| `/settime [dias]` | Define duração | `/settime 45` |
| `/setwallet [endereço]` | Define carteira | `/setwallet bc1q...` |

#### Monitoramento
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `/stats` | Estatísticas do grupo | `/stats` |
| `/logs` | Últimas ações | `/logs` |
| `/admins` | Lista administradores | `/admins` |
| `/backup` | Exporta dados | `/backup` |

## 🏗️ Arquitetura do Projeto

```
src/
├── main.py                 # Ponto de entrada
├── handlers/
│   ├── user_handlers.py    # Comandos de usuário
│   └── admin_handlers.py   # Comandos administrativos
├── models/
│   ├── user.py            # Modelo de usuário
│   ├── admin.py           # Modelo de admin
│   ├── group.py           # Modelo de grupo
│   ├── payment.py         # Modelo de pagamento
│   └── ...                # Outros modelos
├── services/
│   ├── telegram_service.py # Integração Telegram
│   ├── pixgo_service.py   # API PixGo
│   ├── usdt_service.py    # USDT Polygon
│   └── mute_service.py    # Serviço de mute
└── utils/
    ├── config.py          # Configurações
    ├── logger.py          # Sistema de logs
    └── performance.py     # Monitoramento
```

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**: Linguagem principal
- **python-telegram-bot**: Framework para bots Telegram
- **SQLAlchemy**: ORM para banco de dados
- **Alembic**: Migrações de banco de dados
- **Requests**: Cliente HTTP para APIs
- **SQLite/PostgreSQL**: Banco de dados
- **python-dotenv**: Gerenciamento de variáveis de ambiente

## 🧪 Desenvolvimento

### Configuração do Ambiente de Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
pip install -e ".[dev]"

# Executar testes
pytest

# Verificar código
ruff check .
ruff format .

# Executar migrações
alembic upgrade head
```

### Estrutura de Testes

```
tests/
├── unit/              # Testes unitários
├── integration/       # Testes de integração
└── contract/          # Testes de contrato
```

## 🚀 Deploy

### SquareCloud (Recomendado)

1. Faça upload do código
2. Configure as variáveis de ambiente
3. Defina `src/main.py` como arquivo principal
4. Configure Python 3.11+

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "src/main.py"]
```

## 🔧 Solução de Problemas

### Problemas Comuns

**Bot não responde comandos:**
- Verifique se o bot é administrador no grupo
- Confirme o token do Telegram
- Verifique logs por erros

**Pagamentos não funcionam:**
- Valide API key do PixGo
- Verifique webhook URLs
- Confirme saldo da carteira

**Erro de banco de dados:**
- Execute `alembic upgrade head`
- Verifique permissões do arquivo DB
- Reinicie o bot

### Logs e Debug

```bash
# Ver logs em tempo real
tail -f logs/bot.log

# Executar com debug
LOG_LEVEL=DEBUG ./run_bot.sh
```

## 📖 Documentação

- [Guia de Início Rápido](Guide-starter.md) - Tutorial completo
- [Documentação de Comandos](docs/commands.md)
- [Especificações Técnicas](specs/)
- [Plano de Implementação](docs/implementation_plan.md)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código

- **Formatação**: Ruff
- **Commits**: Conventional Commits
- **Testes**: pytest com cobertura >80%
- **Documentação**: Docstrings em todas as funções

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/botclient/issues)
- **Discord**: [Servidor de Suporte](#)
- **Email**: suporte@seudominio.com

## 🙏 Agradecimentos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [PixGo](https://pixgo.org) pela API de pagamentos
- Comunidade Python por todas as bibliotecas

---

**⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!**