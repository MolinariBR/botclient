# 📋 Comandos do Bot

---

## 👑 Administrativos

### Gerenciamento de Membros
- `/add @usuario` — adiciona manualmente um usuário.
- `/kick @usuario` — remove um usuário do grupo.
- `/ban @usuario` — bane permanentemente.
- `/unban @usuario` — remove o banimento.
- `/mute @usuario [tempo]` — silencia o usuário por tempo determinado.
- `/unmute @usuario` — remove o silêncio.
- `/warn @usuario [motivo]` — envia um aviso (com contagem de strikes).
- `/resetwarn @usuario` — zera os avisos do usuário.
- `/userinfo @usuario` — exibe dados do usuário (status, data de entrada, pagamento, etc).

### Controle de Acesso & Assinaturas
- `/check @usuario` — verifica status do pagamento/assinatura.
- `/renew @usuario` — renova manualmente a assinatura.
- `/expire @usuario` — expira manualmente o acesso.
- `/setprice [valor] [moeda]` — define preço da assinatura.
- `/settime [dias]` — define tempo de acesso.
- `/setwallet [endereço]` — define carteira para pagamentos.
- `/pending` — lista usuários com pagamentos pendentes.

### Comunicação & Anúncios
- `/broadcast [mensagem]` — envia uma mensagem para todos os membros.
- `/schedule [hora] [mensagem]` — programa uma mensagem automática.
- `/rules` — envia as regras do grupo.
- `/welcome` — define ou atualiza a mensagem de boas-vindas.
- `/sendto @usuario [mensagem]` — envia mensagem privada para o membro.

### Configurações & Logs
- `/settings` — abre painel de configurações do bot.
- `/admins` — lista todos os administradores.
- `/stats` — mostra estatísticas do grupo (membros, crescimento, engajamento).
- `/logs` — exibe últimas ações do bot (entradas, banimentos, pagamentos).
- `/backup` — exporta lista de membros e dados do grupo.
- `/restore` — importa backup anterior.

---

## 👤 Comandos de Usuário

- `/start` — inicia o bot e mostra o menu principal.
- `/help` — mostra os comandos disponíveis e instruções.
- `/status` — mostra o status do pagamento/acesso do usuário.
- `/pay` — gera link ou QR Code de pagamento.
- `/renew` — renova assinatura automaticamente.
- `/cancel` — cancela a renovação automática.
- `/support` — abre canal de suporte ou contato com admin.
- `/info` — mostra detalhes sobre o grupo/mentoria.
- `/invite` — gera link pessoal de convite (com rastreio de afiliado opcional).

---