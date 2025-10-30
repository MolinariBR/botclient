# 🚀 Guia de Deploy - Square Cloud

## Problema Atual

Se você está vendo erros como:
```
Configuration errors:
- TELEGRAM_TOKEN is required
- PIXGO_API_KEY is required
- USDT_WALLET_ADDRESS is required
```

Isso significa que as variáveis de ambiente não estão configuradas no Square Cloud.

## ✅ Solução DEFINITIVA - Configurar no Painel Square Cloud

### ⚠️ IMPORTANTE: As variáveis DEVEM ser configuradas no PAINEL WEB

**O arquivo `squarecloud.app` pode não funcionar corretamente. Configure manualmente no painel:**

### Passo 1: Acesse o Painel Square Cloud
1. Entre em [squarecloud.app](https://squarecloud.app)
2. Vá para sua aplicação
3. Clique em **"Environment"** ou **"Variáveis de Ambiente"**

### Passo 2: Adicione Cada Variável Individualmente

**Clique em "Add Variable" e adicione uma por vez:**

| Variable Name | Value |
|---------------|--------|
| `TELEGRAM_TOKEN` | `7729659551:AAEFWjED5bU4nCqgwhYpQa4UwvAK99WZ5vA` |
| `PIXGO_API_KEY` | `pk_7e5617a42e9b704d5e320629da68e0097edb718510cf01b3abb6b11bd33d92d9` |
| `PIXGO_BASE_URL` | `https://pixgo.org/api/v1` |
| `USDT_WALLET_ADDRESS` | `0x87C3373E83CDe3640F7b636033D2591ac05b4793` |
| `DATABASE_URL` | `sqlite:///botclient.db` |
| `SUBSCRIPTION_PRICE` | `10.0` |
| `SUBSCRIPTION_DAYS` | `30` |
| `LOG_LEVEL` | `INFO` |
| `LOG_FILE` | `logs/bot.log` |

### Passo 3: Salve e Reinicie
- Clique em **"Save"** para cada variável
- Depois de adicionar todas, **reinicie a aplicação**

### 📱 Verificação
Após reiniciar, você deve ver nos logs:
```
INFO:utils.config:TELEGRAM_TOKEN configured: Yes
INFO:utils.config:PIXGO_API_KEY configured: Yes
INFO:utils.config:USDT_WALLET_ADDRESS configured: Yes
```

### Passo 2: Fazer Redeploy

Após configurar as variáveis, faça um novo deploy da aplicação.

## 🔧 Arquivos Corrigidos

### ✅ squarecloud.app
- Variáveis de ambiente configuradas
- Versão corrigida para "latest"

### ✅ start.sh
- Script mais robusto
- Verificações de ambiente
- Logs detalhados

### ✅ src/utils/config.py
- Logs de debug para configuração
- Melhor diagnóstico de problemas

## 📋 Checklist de Deploy

- [ ] Variáveis de ambiente configuradas no Square Cloud
- [ ] Arquivo `squarecloud.app` atualizado
- [ ] Script `start.sh` com permissões de execução
- [ ] Deploy realizado com sucesso

## 🐛 Troubleshooting

### Erro: "cd: /home/container: No such file or directory"
- ✅ **Resolvido**: Script start.sh agora verifica o diretório correto

### Erro: "Configuration errors"
- ✅ **Solução**: Configure as variáveis de ambiente no painel Square Cloud

### Erro: "Python not found"
- ✅ **Resolvido**: Script detecta automaticamente python/python3

## 📞 Suporte

Se ainda tiver problemas, verifique:
1. Todas as variáveis de ambiente estão configuradas
2. Os valores estão corretos (copie do arquivo .env)
3. O deploy foi feito após as mudanças

## 🐛 Problema Atual: Erro de Rede no Square Cloud

Se você está vendo erros como:
```
telegram.error.NetworkError: httpx.ConnectError
telegram.error.NetworkError: httpx.ReadError
```

Isso significa que o bot está tendo problemas de conectividade com a API do Telegram.

### ✅ Solução Implementada

**O código foi atualizado com:**

1. **Timeouts mais longos** para conexões de rede
2. **Retry logic** com backoff exponencial
3. **Melhor tratamento de erros** de rede
4. **Logs detalhados** para diagnóstico

### 📊 Status Atual

- ✅ **Variáveis de ambiente**: Carregadas com sucesso
- ✅ **Mute service**: Iniciado corretamente
- ❌ **Conectividade Telegram**: Problemas de rede no Square Cloud

### 🔧 Possíveis Causas

1. **Firewall do Square Cloud** bloqueando conexões externas
2. **Problemas de DNS** no ambiente containerizado
3. **Timeouts de rede** muito curtos para o ambiente
4. **Limitações de rede** do plano Square Cloud

### 🚀 Próximos Passos

1. **Aguarde** - O bot agora tem retry automático
2. **Verifique logs** - Procure por melhorias na conectividade
3. **Considere upgrade** do plano Square Cloud se necessário
4. **Teste localmente** - Verifique se o token do Telegram é válido

### � Suporte

Se o problema persistir:
- Verifique se o token do Telegram está correto
- Teste o bot localmente primeiro
- Considere usar um VPS em vez do Square Cloud para bots