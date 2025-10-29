# 🚀 Deploy na SquareCloud - Bot VIP Telegram

## 📋 Pré-requisitos

1. **Conta SquareCloud**: [Criar conta](https://squarecloud.app/pt-br/signin)
2. **Plano pago**: Escolher plano adequado em [Preços](https://squarecloud.app/pt-br/pricing)
3. **Bot Telegram**: Criado via [@BotFather](https://t.me/botfather)
4. **API PixGo**: Conta em [PixGo](https://pixgo.org)
5. **Carteira USDT**: Endereço Polygon (opcional)

## ⚙️ Configuração

### 1. Arquivos Necessários
✅ `squarecloud.app` - Configuração da SquareCloud
✅ `requirements.txt` - Dependências Python
✅ `src/main.py` - Arquivo principal
✅ `start.sh` - Script de inicialização

### 2. Variáveis de Ambiente no Painel SquareCloud

Acesse o painel da SquareCloud e configure as seguintes variáveis:

```bash
# Obrigatórias
TELEGRAM_TOKEN=seu_token_do_botfather
DATABASE_URL=sqlite:///botclient.db

# Pagamentos PIX
PIXGO_API_KEY=sua_chave_pixgo
PIXGO_BASE_URL=https://pixgo.org/api/v1

# Pagamentos USDT (opcional)
USDT_WALLET_ADDRESS=seu_endereco_polygon

# Configurações do Sistema
SUBSCRIPTION_PRICE=50.0
SUBSCRIPTION_DAYS=30
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
```

## 📤 Fazendo o Deploy

### Método 1: Upload via Dashboard

1. **Compactar o projeto**:
   ```bash
   # Excluir arquivos desnecessários
   rm -rf .venv venv .git

   # Criar arquivo zip
   zip -r bot-vip-telegram.zip . -x "*.git*" "*.venv*" "venv/*" "*.log" ".env"
   ```

2. **Fazer upload**:
   - Acesse [Dashboard SquareCloud](https://squarecloud.app/pt-br/upload)
   - Arraste o arquivo `bot-vip-telegram.zip`
   - Clique em "Deploy"

### Método 2: CLI (se disponível)

```bash
# Instalar CLI da SquareCloud
npm install -g @squarecloud/cli

# Fazer login
squarecloud login

# Deploy
squarecloud deploy
```

## 🔧 Pós-Deploy

### 1. Verificar Status
- Acesse o painel SquareCloud
- Verifique se o bot está "Online"
- Monitore logs em tempo real

### 2. Primeiro Admin
Após o deploy, registre o primeiro admin:
```
/add @seu_usuario
```

### 3. Registrar Grupos
Para cada grupo VIP:
```
/register_group
```

## 📊 Monitoramento

### Logs
- **Painel SquareCloud**: Logs em tempo real
- **Arquivo local**: `logs/bot.log` (se configurado)

### Métricas
- **Uptime**: Disponível no painel
- **Uso de RAM**: Monitorado automaticamente
- **Performance**: Logs de performance incluídos

## 🛠️ Solução de Problemas

### Bot não inicia
```
Erro: "No such table: admins"
```
**Solução**: Verificar se migrações foram aplicadas
```bash
# No painel SquareCloud, verificar logs
# Se necessário, executar manualmente:
python -c "from src.main import *; init_db()"
```

### Erro de memória
```
MEMORY ERROR
```
**Solução**: Aumentar RAM no painel (512MB recomendado)

### Token inválido
```
Unauthorized
```
**Solução**: Verificar TELEGRAM_TOKEN no painel

## 💰 Custos

- **Plano Básico**: ~R$ 15-25/mês
- **512MB RAM**: Suficiente para ~1000 usuários ativos
- **Banco SQLite**: Gratuito e integrado

## 📞 Suporte

- **Documentação SquareCloud**: [docs.squarecloud.app](https://docs.squarecloud.app)
- **Suporte**: [Contato](https://docs.squarecloud.app/pt-br/company/support)
- **Discord**: [Servidor](https://discord.gg/squarecloudofc)

## ✅ Checklist Pré-Deploy

- [ ] `squarecloud.app` configurado
- [ ] `requirements.txt` criado
- [ ] `start.sh` com permissões de execução
- [ ] Variáveis de ambiente no painel
- [ ] Arquivos desnecessários excluídos (.venv, .git)
- [ ] Testado localmente
- [ ] Primeiro admin definido
- [ ] Grupos registrados

---

**🎉 Pronto para deploy! Seu bot VIP Telegram estará online em minutos.**