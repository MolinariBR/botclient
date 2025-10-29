# 🚀 Guia de Início Rápido - Bot VIP Telegram

## 📋 Visão Geral

Este é um bot completo para gerenciamento de grupos VIP no Telegram, com sistema de pagamentos via PIX, controle de assinaturas, moderação automática e muito mais.

## 🛠️ Instalação no SquareCloud

### 1. Preparação do Projeto

1. **Clone o repositório:**
   ```bash
   git clone <seu-repositorio>
   cd botclient
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure o ambiente:**
   ```bash
   cp .env.example .env
   # Edite o .env com suas configurações
   ```

### 2. Deploy no SquareCloud

1. **Acesse o painel do SquareCloud**
2. **Clique em "Novo Aplicativo"**
3. **Selecione "Python" como tipo de aplicação**
4. **Configure as seguintes opções:**

   **Configurações Básicas:**
   - **Nome:** Bot VIP Telegram
   - **Versão Python:** 3.11
   - **Arquivo Principal:** `src/main.py`

   **Variáveis de Ambiente:**
   ```
   TELEGRAM_TOKEN=seu_token_aqui
   PIXGO_API_KEY=sua_api_key_aqui
   PIXGO_BASE_URL=https://pixgo.org/api/v1
   USDT_WALLET_ADDRESS=seu_endereco_usdt
   DATABASE_URL=sqlite:///botclient.db
   SUBSCRIPTION_PRICE=50.0
   SUBSCRIPTION_DAYS=30
   LOG_LEVEL=INFO
   LOG_FILE=logs/bot.log
   ```

   **Configurações Avançadas:**
   - **Memória:** 512MB (recomendado)
   - **CPU:** 0.5 vCPU
   - **Auto-scaling:** Habilitado
   - **Health Check:** `/health` (se implementado)

5. **Faça o upload do código**
6. **Clique em "Deploy"**

### 3. Verificação do Deploy

Após o deploy, verifique se o bot está funcionando:
1. Vá no Telegram e procure pelo seu bot
2. Envie `/start` para testar
3. Verifique os logs no painel do SquareCloud

## ⚙️ Configuração Inicial

### 1. Credenciais e API Keys

#### Telegram Bot Token
1. Abra o Telegram e procure por `@BotFather`
2. Envie `/newbot`
3. Siga as instruções para criar seu bot
4. Copie o token fornecido
5. Configure no SquareCloud: `TELEGRAM_TOKEN=seu_token`

#### PixGo API Key
1. Acesse [PixGo](https://pixgo.org)
2. Crie uma conta
3. Vá para configurações de API
4. Gere uma nova API Key
5. Configure no SquareCloud: `PIXGO_API_KEY=sua_api_key`

#### USDT Wallet Address
1. Configure seu endereço de carteira USDT
2. Configure no SquareCloud: `USDT_WALLET_ADDRESS=seu_endereco`

### 2. Configurações do Sistema

As seguintes configurações podem ser ajustadas via variáveis de ambiente:

```bash
# Preço padrão da assinatura (em reais)
SUBSCRIPTION_PRICE=50.0

# Duração padrão da assinatura (em dias)
SUBSCRIPTION_DAYS=30

# Nível de logging
LOG_LEVEL=INFO

# Arquivo de log
LOG_FILE=logs/bot.log
```

## 👑 Configuração de Administradores

### Registrar Primeiro Admin

1. **No Telegram, inicie uma conversa privada com seu bot**
2. **Envie o comando:**
   ```
   /add @seu_usuario
   ```
   *Substitua `@seu_usuario` pelo seu username do Telegram*

3. **Verifique se foi registrado:**
   ```
   /admins
   ```

### Adicionar Mais Administradores

Como admin, você pode adicionar outros admins:
```
/add @usuario_admin
```

## 📱 Configuração de Grupos

### Registrar um Grupo

1. **Adicione o bot como administrador no grupo**
2. **No grupo, envie:**
   ```
   /register_group
   ```

3. **O bot confirmará o registro**

### Verificar ID do Grupo

Para ver o ID de qualquer grupo:
```
/group_id
```

## 💰 Configuração de Preços e Planos

### Atualizar Preço da Assinatura

Como admin, use:
```
/setprice 75.50 BRL
```
*Exemplo: Define o preço como R$ 75,50*

### Atualizar Duração da Assinatura

Como admin, use:
```
/settime 45
```
*Exemplo: Define a duração como 45 dias*

### Configurar Carteira de Pagamento

Como admin, use:
```
/setwallet bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
```
*Exemplo: Define endereço Bitcoin*

## 📚 Lista Completa de Comandos

### 🤖 Comandos Gerais

- `/start` — Inicia o bot e mostra informações básicas
- `/help` — Mostra todos os comandos disponíveis
- `/pay` — Inicia processo de pagamento da assinatura VIP
- `/status` — Verifica status da sua assinatura
- `/renew` — Renova assinatura automaticamente
- `/cancel` — Cancela renovação automática
- `/support` — Abre canal de suporte com administradores
- `/info` — Mostra informações sobre o grupo/mentoria
- `/invite` — Gera link pessoal de convite

### 👑 Comandos Administrativos

#### Gerenciamento de Membros
- `/add @usuario` — Adiciona usuário manualmente ao VIP
- `/kick @usuario` — Remove usuário do grupo
- `/ban @usuario` — Bane permanentemente
- `/unban @usuario` — Remove banimento
- `/mute @usuario [tempo]` — Silencia usuário (ex: `/mute @user 1h`)
- `/unmute @usuario` — Remove silêncio
- `/warn @usuario [motivo]` — Aplica aviso (ex: `/warn @user Spam`)
- `/resetwarn @usuario` — Zera avisos do usuário
- `/userinfo @usuario` — Mostra dados detalhados do usuário

#### Controle de Assinaturas
- `/check @usuario` — Verifica status de pagamento
- `/renew @usuario` — Renova assinatura manualmente
- `/expire @usuario` — Expira acesso manualmente
- `/pending` — Lista usuários com pagamentos pendentes

#### Comunicação e Anúncios
- `/broadcast [mensagem]` — Envia mensagem para todos os membros
- `/schedule [hora] [mensagem]` — Programa mensagem (ex: `/schedule 14:00 Promoção especial!`)
- `/rules` — Envia regras do grupo
- `/welcome` — Define mensagem de boas-vindas
- `/sendto @usuario [mensagem]` — Envia mensagem privada

#### Configurações do Sistema
- `/setprice [valor] [moeda]` — Define preço (ex: `/setprice 100.00 BRL`)
- `/settime [dias]` — Define duração (ex: `/settime 60`)
- `/setwallet [endereço]` — Define carteira de pagamento

#### Monitoramento e Logs
- `/settings` — Abre painel de configurações
- `/admins` — Lista todos os administradores
- `/stats` — Mostra estatísticas do grupo
- `/logs` — Exibe últimas ações do bot
- `/backup` — Exporta dados do grupo
- `/restore` — Importa backup

#### Utilitários
- `/register_group` — Registra grupo atual
- `/group_id` — Mostra ID do grupo atual

## 📖 Como Usar Cada Comando

### Para Usuários Comuns

#### `/start`
- **Onde usar:** Grupos ou privado
- **Função:** Apresenta o bot e mostra informações básicas
- **Exemplo:** Apenas envie `/start`

#### `/pay`
- **Onde usar:** Grupos
- **Função:** Inicia processo de pagamento via PIX ou USDT
- **Exemplo:** `/pay`
- **Nota:** O bot enviará QR Code e instruções

#### `/status`
- **Onde usar:** Grupos
- **Função:** Mostra status da sua assinatura
- **Exemplo:** `/status`
- **Informações:** Data de expiração, status ativo/inativo

#### `/renew`
- **Onde usar:** Grupos
- **Função:** Renova assinatura automaticamente
- **Exemplo:** `/renew`
- **Nota:** Deve ter assinatura ativa

#### `/cancel`
- **Onde usar:** Grupos
- **Função:** Cancela renovação automática
- **Exemplo:** `/cancel`

#### `/support`
- **Onde usar:** Grupos
- **Função:** Contato com administradores
- **Exemplo:** `/support`

#### `/info`
- **Onde usar:** Grupos
- **Função:** Informações sobre o grupo/mentoria
- **Exemplo:** `/info`

#### `/invite`
- **Onde usar:** Grupos
- **Função:** Gera link de convite pessoal
- **Exemplo:** `/invite`

### Para Administradores

#### Gerenciamento de Usuários

##### `/add @usuario`
- **Função:** Adiciona usuário ao VIP manualmente
- **Exemplo:** `/add @johndoe`
- **Nota:** Dá acesso VIP sem pagamento

##### `/kick @usuario`
- **Função:** Remove usuário do grupo
- **Exemplo:** `/kick @spammer`
- **Nota:** Não remove VIP, apenas do grupo

##### `/ban @usuario`
- **Função:** Banimento permanente
- **Exemplo:** `/ban @violador`
- **Nota:** Remove VIP e bane do grupo

##### `/unban @usuario`
- **Função:** Remove banimento
- **Exemplo:** `/unban @usuario`
- **Nota:** Permite entrada novamente

##### `/mute @usuario [tempo]`
- **Função:** Silencia usuário temporariamente
- **Exemplo:** `/mute @flooder 30m`
- **Formatos de tempo:** `30s`, `5m`, `2h`, `1d`

##### `/warn @usuario [motivo]`
- **Função:** Aplica aviso ao usuário
- **Exemplo:** `/warn @user Spam no grupo`
- **Nota:** Sistema de strikes automático

##### `/userinfo @usuario`
- **Função:** Informações detalhadas
- **Exemplo:** `/userinfo @user`
- **Informações:** Status VIP, data entrada, pagamentos, avisos

#### Controle de Pagamentos

##### `/check @usuario`
- **Função:** Verifica status de pagamento
- **Exemplo:** `/check @user`
- **Informações:** Status, valor, data

##### `/renew @usuario`
- **Função:** Renova VIP manualmente
- **Exemplo:** `/renew @user`

##### `/expire @usuario`
- **Função:** Expira acesso VIP
- **Exemplo:** `/expire @user`

##### `/pending`
- **Função:** Lista pagamentos pendentes
- **Exemplo:** `/pending`

#### Comunicação

##### `/broadcast [mensagem]`
- **Função:** Mensagem para todos os membros
- **Exemplo:** `/broadcast Manutenção hoje às 22h`

##### `/schedule [hora] [mensagem]`
- **Função:** Programa mensagem automática
- **Exemplo:** `/schedule 15:30 Lembrete: aula hoje!`

##### `/sendto @usuario [mensagem]`
- **Função:** Mensagem privada para usuário
- **Exemplo:** `/sendto @user Sua assinatura expira em 3 dias`

#### Configurações

##### `/setprice [valor] [moeda]`
- **Função:** Define preço da assinatura
- **Exemplo:** `/setprice 89.90 BRL`

##### `/settime [dias]`
- **Função:** Define duração da assinatura
- **Exemplo:** `/settime 45`

##### `/setwallet [endereço]`
- **Função:** Define carteira para pagamentos
- **Exemplo:** `/setwallet 0x1234567890abcdef`

#### Monitoramento

##### `/stats`
- **Função:** Estatísticas do grupo
- **Informações:** Total membros, crescimento, engajamento

##### `/logs`
- **Função:** Últimas ações do bot
- **Informações:** Entradas, banimentos, pagamentos

##### `/backup`
- **Função:** Exporta dados do grupo
- **Resultado:** Arquivo com todos os dados

## 🔧 Solução de Problemas

### Bot não responde
1. Verifique se está online no SquareCloud
2. Confirme o token do Telegram
3. Verifique logs no painel

### Pagamentos não funcionam
1. Verifique API Key do PixGo
2. Confirme webhook URL se necessário
3. Verifique saldo da carteira

### Comandos não funcionam
1. Certifique-se de que o bot é admin no grupo
2. Verifique permissões do usuário
3. Use `/help` para confirmar sintaxe

### Erro de banco de dados
1. Verifique se migrações foram aplicadas
2. Reinicie o bot no SquareCloud
3. Verifique logs por erros SQL

## 📞 Suporte

Para suporte técnico:
1. Use `/support` no bot
2. Verifique logs no SquareCloud
3. Consulte documentação completa em `/docs`

---

**Última atualização:** Outubro 2025
**Versão:** 1.0.0