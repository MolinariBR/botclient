# 📋 Comandos do Bot

---

## 👑 Administrativos

### Gerenciamento de Membros
- `/add @usuario` — adiciona manualmente um usuário. [X]
- `/kick @usuario` — remove um usuário do grupo. [X]
- `/ban @usuario` — bane permanentemente. [X]
- `/unban @usuario` — remove o banimento. [X]
- `/mute @usuario [tempo]` — silencia o usuário por tempo determinado. [X]
- `/unmute @usuario` — remove o silêncio. [X]
- `/warn @usuario [motivo]` — envia um aviso (com contagem de strikes). [X]
- `/resetwarn @usuario` — zera os avisos do usuário. [X]
- `/userinfo @usuario` — exibe dados do usuário (status, data de entrada, pagamento, etc). [X]

### Controle de Acesso & Assinaturas
- `/check @usuario` — verifica status do pagamento/assinatura. [X]
- `/renew @usuario` — renova manualmente a assinatura. [X]
- `/expire @usuario` — expira manualmente o acesso. [X]
- `/setprice [valor] [moeda]` — define preço da assinatura. [X]
- `/settime [dias]` — define tempo de acesso. [X]
- `/setwallet [endereço]` — define carteira para pagamentos. [X]
- `/pending` — lista usuários com pagamentos pendentes. [X]

### Comunicação & Anúncios
- `/broadcast [mensagem]` — envia uma mensagem para todos os membros. [X]
- `/schedule [hora] [mensagem]` — programa uma mensagem automática. [X]
- `/rules` — envia as regras do grupo. [X]
- `/welcome` — define ou atualiza a mensagem de boas-vindas. [X]
- `/sendto @usuario [mensagem]` — envia mensagem privada para o membro. [X]

### Configurações & Logs
- `/settings` — abre painel de configurações do bot. [X]
- `/admins` — lista todos os administradores. [X]
- `/stats` — mostra estatísticas do grupo (membros, crescimento, engajamento). [X]
- `/logs` — exibe últimas ações do bot (entradas, banimentos, pagamentos). [X]
- `/backup` — exporta lista de membros e dados do grupo. [X]
- `/restore` — importa backup anterior. [X]

---

## 👤 Comandos de Usuário

- `/start` — inicia o bot e mostra o menu principal. [X]
- `/help` — mostra os comandos disponíveis e instruções. [X]
- `/status` — mostra o status do pagamento/acesso do usuário. [X]
- `/renew` — renova assinatura automaticamente. [X]
- `/cancel` — cancela a renovação automática. [X]
- `/support` — abre canal de suporte ou contato com admin. [X]
- `/info` — mostra detalhes sobre o grupo/mentoria. [X]
- `/invite` — gera link pessoal de convite (com rastreio de afiliado opcional). [X]

---

## 📝 Notas

- **Comando /help**: Use `/help` para ver todos os comandos disponíveis diretamente no bot. O comando mostra diferentes opções dependendo se você é admin ou usuário comum.
- **Status [X]**: Indica que o comando foi implementado e está funcional.
- **Grupos vs Privado**: A maioria dos comandos funciona apenas em grupos. Use `/start` no privado para informações básicas.