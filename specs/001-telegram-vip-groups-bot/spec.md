# Feature Specification: Bot Telegram para Gestão de Grupos VIPs

**Feature Branch**: `001-telegram-vip-groups-bot`  
**Created**: 2025-10-28  
**Status**: Draft  
**Input**: Implementar bot Telegram para gestão de grupos VIP com assinaturas via PIX usando API PixGo e suporte a USDT Polygon.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Usuário paga assinatura via PIX (Priority: P1)

Como usuário comum, quero gerar um QR Code de pagamento via PIX para acessar o grupo VIP.

**Why this priority**: Essencial para monetização e acesso ao serviço.

**Independent Test**: Pode ser testado gerando QR e verificando se pagamento é processado.

**Acceptance Scenarios**:

1. **Given** usuário não tem assinatura ativa, **When** executa /pay, **Then** recebe QR Code e link de pagamento.
2. **Given** pagamento é confirmado, **When** usuário entra no grupo, **Then** é admitido automaticamente.

---

### User Story 2 - Admin adiciona usuário manualmente (Priority: P2)

Como administrador, quero adicionar um usuário ao grupo VIP manualmente.

**Why this priority**: Controle administrativo necessário.

**Independent Test**: Testado adicionando usuário e verificando acesso.

**Acceptance Scenarios**:

1. **Given** admin executa /add @usuario, **When** usuário tenta entrar, **Then** é admitido.

---

### User Story 3 - Admin verifica status de pagamento (Priority: P3)

Como administrador, quero verificar o status de pagamento de um usuário.

**Why this priority**: Monitoramento de assinaturas.

**Independent Test**: Testado consultando status e comparando com dados reais.

**Acceptance Scenarios**:

1. **Given** usuário pagou, **When** admin executa /check @usuario, **Then** mostra status "completed".

### User Story 5 - Admin remove usuário do grupo (Priority: P2)

Como administrador, quero remover um usuário do grupo VIP.

**Why this priority**: Controle administrativo básico.

**Independent Test**: Testado removendo usuário e verificando saída do grupo.

**Acceptance Scenarios**:

1. **Given** usuário está no grupo, **When** admin executa /kick @usuario, **Then** usuário é removido.

---

### User Story 6 - Admin bane usuário permanentemente (Priority: P2)

Como administrador, quero banir um usuário permanentemente.

**Why this priority**: Controle de acesso rigoroso.

**Independent Test**: Testado banindo usuário e impedindo reentrada.

**Acceptance Scenarios**:

1. **Given** usuário está no grupo, **When** admin executa /ban @usuario, **Then** usuário é banido permanentemente.

---

### User Story 7 - Admin silencia usuário (Priority: P3)

Como administrador, quero silenciar um usuário por tempo determinado.

**Why this priority**: Moderação de grupo.

**Independent Test**: Testado silenciando e verificando se mensagens são bloqueadas.

**Acceptance Scenarios**:

1. **Given** usuário está ativo, **When** admin executa /mute @usuario 10, **Then** usuário não pode enviar mensagens por 10 minutos.

---

### User Story 8 - Admin envia broadcast para membros (Priority: P3)

Como administrador, quero enviar mensagem para todos os membros.

**Why this priority**: Comunicação em massa.

**Independent Test**: Testado enviando broadcast e verificando recebimento por membros.

**Acceptance Scenarios**:

1. **Given** admin define horário, **When** executa /schedule "12:00" "mensagem", **Then** mensagem é enviada automaticamente às 12:00.
2. **Given** horário passado, **When** sistema verifica, **Then** mensagem é enviada via cron job interno.

---

### User Story 9 - Usuário vê status de assinatura (Priority: P3)

Como usuário, quero ver meu status de pagamento e acesso.

**Why this priority**: Transparência para usuário.

**Independent Test**: Testado executando /status e vendo informações corretas.

**Acceptance Scenarios**:

1. **Given** usuário tem assinatura, **When** executa /status, **Then** vê data de expiração e status.

---

### User Story 10 - Usuário obtém ajuda (Priority: P3)

Como usuário, quero ver comandos disponíveis.

**Why this priority**: Orientação inicial.

**Independent Test**: Testado executando /help e vendo lista de comandos.

**Acceptance Scenarios**:

1. **Given** usuário interage com bot, **When** executa /help, **Then** vê instruções e comandos disponíveis.

---

### User Story 11 - Usuário gera link de convite (Priority: P3)

Como usuário, quero gerar link de convite pessoal.

**Why this priority**: Incentiva compartilhamento.

**Independent Test**: Executar /invite e verificar link gerado.

**Acceptance Scenarios**:

1. **Given** usuário ativo, **When** executa /invite, **Then** recebe link único com rastreio.

### Edge Cases

- Pagamento expirado: Usuário não consegue acessar após 20 minutos sem confirmação.
- Usuário banido: Não pode executar comandos mesmo com assinatura.
- Múltiplos pagamentos pendentes: Sistema prioriza o mais recente.
- Erro na API PixGo: Bot informa usuário para tentar novamente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema MUST permitir usuários gerarem QR Code de pagamento via PIX.
- **FR-002**: Sistema MUST integrar com API PixGo para criar e consultar pagamentos.
- **FR-003**: Sistema MUST suportar endereço USDT Polygon fixo para pagamentos alternativos.
- **FR-004**: Sistema MUST restringir comandos administrativos apenas a admins no chat direto.
- **FR-005**: Sistema MUST permitir apenas usuários comuns interagirem no grupo VIP.
- **FR-006**: Sistema MUST gerenciar membros: add, kick, ban, mute, warn, resetwarn, unban, unmute, userinfo.
- **FR-007**: Sistema MUST controlar assinaturas: check, renew, expire, setprice, settime, setwallet, pending.
- **FR-008**: Sistema MUST fornecer comunicação: broadcast, schedule, rules, welcome, sendto.
- **FR-009**: Sistema MUST oferecer configurações e logs: settings, admins, stats, logs, backup, restore.
- **FR-010**: Sistema MUST permitir comandos de usuário: start, help, status, pay, renew, cancel, support, info, invite.

### Key Entities *(include if feature involves data)*

- **Usuário**: Representa membro do Telegram, com ID, nome, status de assinatura, data de entrada.
- **Pagamento**: Vinculado a usuário, com ID PixGo, valor, status, data de criação/expiração.
- **Grupo**: Grupo VIP no Telegram, com ID, admins, regras, configurações.
- **Admin**: Usuário com permissões administrativas, pode executar comandos admin.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuários conseguem gerar QR de pagamento em menos de 30 segundos.
- **SC-002**: 95% dos pagamentos confirmados levam a admissão automática no grupo em menos de 1 minuto.
- **SC-003**: Admins conseguem verificar status de qualquer usuário em menos de 10 segundos.
- **SC-004**: Sistema suporta até 1000 conexões ativas simultâneas e processa 500 mensagens por minuto sem degradação.
- **SC-005**: Taxa de erro em integrações com PixGo abaixo de 1%.

## Assumptions

- API PixGo funciona conforme documentação.
- Token Telegram é válido e bot tem permissões necessárias.
- Endereço USDT Polygon é fixo e seguro.
- Usuários têm app de banco compatível com PIX.
