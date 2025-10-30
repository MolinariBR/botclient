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

## ✅ Solução Rápida

### Passo 1: Configurar Variáveis no Painel Square Cloud

1. **Acesse o painel da Square Cloud**
2. **Vá para sua aplicação**
3. **Clique em "Environment" ou "Variáveis de Ambiente"**
4. **Adicione as seguintes variáveis:**

```bash
TELEGRAM_TOKEN=7729659551:AAEFWjED5bU4nCqgwhYpQa4UwvAK99WZ5vA
PIXGO_API_KEY=pk_7e5617a42e9b704d5e320629da68e0097edb718510cf01b3abb6b11bd33d92d9
PIXGO_BASE_URL=https://pixgo.org/api/v1
USDT_WALLET_ADDRESS=0x87C3373E83CDe3640F7b636033D2591ac05b4793
DATABASE_URL=sqlite:///botclient.db
SUBSCRIPTION_PRICE=10.0
SUBSCRIPTION_DAYS=30
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
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

**O bot deve funcionar perfeitamente após configurar as variáveis!** 🚀