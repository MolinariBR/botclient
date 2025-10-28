# 📋 Plano de Implementação - Novos Comandos do Bot

**Data:** 28 de outubro de 2025  
**Status:** Planejamento  
**Total de comandos a implementar:** 23  

---

## 🎯 Visão Geral

Este documento detalha o plano de implementação dos comandos faltantes listados em `commands.md`. Os comandos estão organizados por prioridade e categoria para facilitar o desenvolvimento incremental.

### 📊 Estatísticas
- **Comandos Admin:** 20
- **Comandos Usuário:** 3
- **Total:** 23 comandos

---

## 🔥 Prioridade 1: Essenciais (Implementar Primeiro)

### Gerenciamento Básico de Membros
1. **`/unban @usuario`** - Remove banimento
   - **Descrição:** Remove o banimento permanente de um usuário
   - **Implementação:** Atualizar `is_banned = False` no banco
   - **Dependências:** Modelo User com campo `is_banned`
   - **Arquivo:** `admin_handlers.py`

2. **`/unmute @usuario`** - Remove silêncio
   - **Descrição:** Remove o silêncio temporário de um usuário
   - **Implementação:** Limpar `mute_until` e `is_muted = False`
   - **Dependências:** Campos `mute_until`, `is_muted` no User
   - **Arquivo:** `admin_handlers.py`

3. **`/userinfo @usuario`** - Informações detalhadas do usuário
   - **Descrição:** Exibe status completo (pagamento, entrada, ban/mute, etc)
   - **Implementação:** Query User + Payment + GroupMembership
   - **Dependências:** Todos os modelos (User, Payment, Group)
   - **Arquivo:** `admin_handlers.py`

### Controle de Assinaturas
4. **`/pending`** - Lista pagamentos pendentes
   - **Descrição:** Mostra usuários com pagamentos aguardando confirmação
   - **Implementação:** Query payments com status 'pending'
   - **Dependências:** Modelo Payment com status
   - **Arquivo:** `admin_handlers.py`

---

## ⚡ Prioridade 2: Importantes (Funcionalidades Core)

### Avisos e Moderação
5. **`/warn @usuario [motivo]`** - Sistema de avisos
   - **Descrição:** Envia aviso com contagem de strikes
   - **Implementação:** Adicionar campo `warn_count` ao User, incrementar
   - **Dependências:** Novo campo no modelo User
   - **Arquivo:** `admin_handlers.py`

6. **`/resetwarn @usuario`** - Zerar avisos
   - **Descrição:** Reseta contador de avisos do usuário
   - **Implementação:** `warn_count = 0`
   - **Dependências:** Campo `warn_count`
   - **Arquivo:** `admin_handlers.py`

### Controle de Acesso
7. **`/expire @usuario`** - Expirar acesso manualmente
   - **Descrição:** Força expiração da assinatura
   - **Implementação:** Atualizar `expires_at` para passado
   - **Dependências:** Campo `expires_at` no User
   - **Arquivo:** `admin_handlers.py`

### Comunicação
8. **`/sendto @usuario [mensagem]`** - Mensagem privada
   - **Descrição:** Envia mensagem direta para um usuário específico
   - **Implementação:** Usar `telegram.send_message()` com user.telegram_id
   - **Dependências:** User.telegram_id válido
   - **Arquivo:** `admin_handlers.py`

---

## 🔧 Prioridade 3: Avançadas (Configurações e Utilitários)

### Configurações do Sistema
9. **`/setprice [valor] [moeda]`** - Definir preço
   - **Descrição:** Atualiza preço da assinatura
   - **Implementação:** Salvar em config ou banco
   - **Dependências:** Sistema de configuração persistente
   - **Arquivo:** `admin_handlers.py`

10. **`/settime [dias]`** - Definir duração
    - **Descrição:** Atualiza dias da assinatura
    - **Implementação:** Salvar configuração
    - **Dependências:** Configuração persistente
    - **Arquivo:** `admin_handlers.py`

11. **`/setwallet [endereço]`** - Definir carteira
    - **Descrição:** Atualiza endereço da carteira USDT
    - **Implementação:** Salvar configuração
    - **Dependências:** Configuração persistente
    - **Arquivo:** `admin_handlers.py`

### Conteúdo e Regras
12. **`/rules`** - Enviar regras
    - **Descrição:** Envia mensagem com regras do grupo
    - **Implementação:** Mensagem pré-definida ou configurável
    - **Dependências:** Armazenamento de regras
    - **Arquivo:** `admin_handlers.py`

13. **`/welcome`** - Configurar boas-vindas
    - **Descrição:** Define mensagem de boas-vindas para novos membros
    - **Implementação:** Salvar mensagem no banco/config
    - **Dependências:** Handler de novos membros
    - **Arquivo:** `admin_handlers.py`

### Agendamento
14. **`/schedule [hora] [mensagem]`** - Mensagem programada
    - **Descrição:** Agenda envio automático de mensagem
    - **Implementação:** Sistema de agendamento (thread/cron)
    - **Dependências:** Scheduler assíncrono
    - **Arquivo:** `admin_handlers.py`

---

## 📊 Prioridade 4: Analytics e Monitoramento

### Estatísticas
15. **`/stats`** - Estatísticas do grupo
    - **Descrição:** Mostra métricas (membros, crescimento, engajamento)
    - **Implementação:** Queries complexas no banco
    - **Dependências:** Dados históricos
    - **Arquivo:** `admin_handlers.py`

16. **`/logs`** - Histórico de ações
    - **Descrição:** Exibe últimas ações (entradas, banimentos, pagamentos)
    - **Implementação:** Sistema de logging estruturado
    - **Dependências:** Tabela de logs
    - **Arquivo:** `admin_handlers.py`

### Administração
17. **`/admins`** - Lista administradores
    - **Descrição:** Mostra todos os admins do bot
    - **Implementação:** Query tabela Admin
    - **Dependências:** Modelo Admin
    - **Arquivo:** `admin_handlers.py`

18. **`/settings`** - Painel de configurações
    - **Descrição:** Interface para configurar bot
    - **Implementação:** InlineKeyboard com opções
    - **Dependências:** Múltiplas configurações
    - **Arquivo:** `admin_handlers.py`

---

## 💾 Prioridade 5: Backup e Manutenção

### Backup
19. **`/backup`** - Exportar dados
    - **Descrição:** Exporta membros e dados em arquivo
    - **Implementação:** Gerar JSON/CSV dos dados
    - **Dependências:** Sistema de arquivos
    - **Arquivo:** `admin_handlers.py`

20. **`/restore`** - Importar backup
    - **Descrição:** Restaura dados de backup
    - **Implementação:** Parser de arquivo + inserts
    - **Dependências:** Validação de dados
    - **Arquivo:** `admin_handlers.py`

---

## 👤 Prioridade 6: Comandos de Usuário

21. **`/cancel`** - Cancelar renovação
    - **Descrição:** Cancela renovação automática da assinatura
    - **Implementação:** Flag `auto_renew = False`
    - **Dependências:** Campo `auto_renew` no User
    - **Arquivo:** `user_handlers.py`

22. **`/support`** - Suporte
    - **Descrição:** Abre contato com admin ou canal de suporte
    - **Implementação:** Link ou forward para admin
    - **Dependências:** Configuração de suporte
    - **Arquivo:** `user_handlers.py`

23. **`/info`** - Informações do grupo
    - **Descrição:** Mostra detalhes sobre o grupo/mentoria
    - **Implementação:** Mensagem pré-definida
    - **Dependências:** Conteúdo configurável
    - **Arquivo:** `user_handlers.py`

---

## 🛠️ Plano de Execução

### Fase 1: Essenciais (1-4)
- **Tempo estimado:** 2-3 dias
- **Comandos:** unban, unmute, userinfo, pending
- **Impacto:** Funcionalidades básicas de moderação

### Fase 2: Importantes (5-8)
- **Tempo estimado:** 3-4 dias
- **Comandos:** warn/resetwarn, expire, sendto
- **Impacto:** Sistema completo de moderação

### Fase 3: Avançadas (9-14)
- **Tempo estimado:** 4-5 dias
- **Comandos:** setprice/settime/setwallet, rules, welcome, schedule
- **Impacto:** Customização e automação

### Fase 4: Analytics (15-18)
- **Tempo estimado:** 3-4 dias
- **Comandos:** stats, logs, admins, settings
- **Impacto:** Monitoramento e administração

### Fase 5: Backup (19-20)
- **Tempo estimado:** 2-3 dias
- **Comandos:** backup, restore
- **Impacto:** Segurança de dados

### Fase 6: Usuário (21-23)
- **Tempo estimado:** 2 dias
- **Comandos:** cancel, support, info
- **Impacto:** UX completa para usuários

### 📋 Checklist de Dependências
- [ ] Novos campos no modelo User: `warn_count`, `auto_renew`
- [ ] Sistema de configuração persistente
- [ ] Handler para novos membros (welcome)
- [ ] Sistema de logging estruturado
- [ ] Scheduler para mensagens programadas
- [ ] Validação de dados para backup/restore

---

## 🎯 Critérios de Aceitação

- ✅ Comando responde corretamente
- ✅ Validação de permissões (admin)
- ✅ Tratamento de erros
- ✅ Logging adequado
- ✅ Documentação no /help
- ✅ Testes básicos funcionais

**Próximo passo:** Implementar comandos da Fase 1 começando por `/unban` e `/unmute`.</content>
<parameter name="filePath">/home/mau/bot/botclient/docs/implementation_plan.md