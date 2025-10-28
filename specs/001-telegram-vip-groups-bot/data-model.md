# Data Model: Bot Telegram para Gestão de Grupos VIPs

## Entities

### Usuário
- **Fields**:
  - id: Integer (primary key)
  - telegram_id: String (unique)
  - name: String
  - status_assinatura: Enum (ativo, expirado, pendente)
  - data_entrada: DateTime
  - data_expiracao: DateTime
  - is_banned: Boolean (default False)
  - mute_until: DateTime (nullable)
  - warnings_count: Integer (default 0)
- **Relationships**: belongs to Grupo, has many Pagamentos
- **Validation**: telegram_id obrigatório, único

### Pagamento
- **Fields**:
  - id: Integer (primary key)
  - user_id: Integer (foreign key to Usuário)
  - pixgo_id: String
  - valor: Float
  - status: Enum (pending, completed, expired, cancelled)
  - data_criacao: DateTime
  - data_expiracao: DateTime
- **Relationships**: belongs to Usuário
- **Validation**: valor >= 10.00, pixgo_id único

### Grupo
- **Fields**:
  - id: Integer (primary key)
  - telegram_group_id: String (unique)
  - nome: String
  - regras: Text
  - preco_assinatura: Float
  - tempo_assinatura_dias: Integer
  - welcome_message: Text
- **Relationships**: has many Usuários, has many Admins
- **Validation**: telegram_group_id obrigatório

### Admin
- **Fields**:
  - id: Integer (primary key)
  - user_id: Integer (foreign key to Usuário)
  - group_id: Integer (foreign key to Grupo)
- **Relationships**: belongs to Usuário, belongs to Grupo
- **Validation**: user_id único por group_id

## State Transitions

### Assinatura Usuário
- pendente → ativo (pagamento completed)
- ativo → expirado (data_expiracao passada)
- expirado → ativo (renovação)

### Pagamento
- pending → completed (PixGo confirma)
- pending → expired (20 min sem confirmação)
- pending → cancelled (usuário cancela)