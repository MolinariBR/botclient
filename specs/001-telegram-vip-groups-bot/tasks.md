**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python project with python-telegram-bot, requests, sqlalchemy dependencies
- [ ] T003 [P] Configure linting and formatting tools (ruff)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup PostgreSQL schema and SQLAlchemy models base
- [X] T005 [P] Implement base services structure (telegram, pixgo, usdt)
- [X] T006 [P] Setup logging infrastructure in src/utils/logger.py
- [X] T007 Configure environment configuration management in src/utils/config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Usuário paga assinatura via PIX (Priority: P1) 🎯 MVP

**Goal**: Permitir usuário gerar QR Code de pagamento PIX para acessar grupo VIP

**Independent Test**: Executar /pay no bot e verificar se QR é gerado e pagamento pode ser processado

### Implementation for User Story 1

- [X] T008 [US1] Implement PixGo service in src/services/pixgo_service.py
- [X] T009 [US1] Create Payment model in src/models/payment.py
- [X] T010 [US1] Implement /pay handler in src/handlers/user_handlers.py
- [X] T011 [US1] Add payment status checking and user admission logic
- [X] T012 [US1] Implement USDT Polygon integration in src/services/usdt_service.py

### Testing for User Story 1

- [X] T008-test [US1] Create unit tests for PixGo service API calls
- [X] T009-test [US1] Create integration tests for payment creation and QR generation
- [X] T010-test [US1] Create handler tests for /pay command responses
- [X] T011-test [US1] Create integration tests for payment status checking
- [X] T012-test [US1] Create unit tests for USDT service

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Admin adiciona usuário manualmente (Priority: P2)

**Goal**: Permitir admin adicionar usuário ao grupo VIP manualmente

**Independent Test**: Admin executa /add @usuario e verifica se usuário é admitido no grupo

### Implementation for User Story 2

- [X] T013 [US2] Create User model in src/models/user.py
- [X] T014 [US2] Create Group model in src/models/group.py
- [X] T015 [US2] Implement /add handler in src/handlers/admin_handlers.py
- [X] T016 [US2] Add group membership management logic

### Testing for User Story 2

- [x] T013-test [US2] Create unit tests for User model
- [x] T014-test [US2] Create unit tests for Group and GroupMembership models
- [x] T015-test [US2] Create handler tests for /add command
- [x] T016-test [US2] Create integration tests for group membership management

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Admin verifica status de pagamento (Priority: P3)

**Goal**: Permitir admin verificar status de pagamento de usuário

**Independent Test**: Admin executa /check @usuario e vê status correto

### Implementation for User Story 3

- [X] T017 [US3] Implement /check handler in src/handlers/admin_handlers.py
- [X] T018 [US3] Add payment status query logic

### Testing for User Story 3

- [x] T017-test [US3] Create handler tests for /check command
- [x] T018-test [US3] Create integration tests for payment status queries

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Usuário renova assinatura (Priority: P3)

**Goal**: Permitir usuário renovar assinatura automaticamente

**Independent Test**: Usuário executa /renew e acesso é estendido

### Implementation for User Story 4

- [X] T019 [US4] Implement /renew handler in src/handlers/user_handlers.py
- [X] T020 [US4] Add subscription renewal logic

### Testing for User Story 4

- [x] T019-test [US4] Create handler tests for /renew command
- [x] T020-test [US4] Create integration tests for subscription renewal flow

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: User Story 5 - Admin remove usuário do grupo (Priority: P2)

**Goal**: Permitir admin remover usuário do grupo VIP

**Independent Test**: Admin executa /kick @usuario e verifica remoção

### Implementation for User Story 5

- [X] T025 [US5] Implement /kick handler in src/handlers/admin_handlers.py
- [X] T026 [US5] Add user removal logic

### Testing for User Story 5

- [X] T021-test [US5] Create handler tests for /kick command
- [X] T022-test [US5] Create integration tests for user removal and group access revocation

---

## Phase 8: User Story 6 - Admin bane usuário permanentemente (Priority: P2)

**Goal**: Permitir admin banir usuário permanentemente

**Independent Test**: Admin executa /ban @usuario e impede reentrada

### Implementation for User Story 6

- [X] T023 [US6] Implement /ban handler in src/handlers/admin_handlers.py
- [X] T024 [US6] Add ban logic and reentry prevention

### Testing for User Story 6

- [X] T023-test [US6] Create handler tests for /ban command
- [X] T024-test [US6] Create integration tests for ban logic and reentry prevention

---

## Phase 9: User Story 7 - Admin silencia usuário (Priority: P3)

**Goal**: Permitir admin silenciar usuário temporariamente

**Independent Test**: Admin executa /mute @usuario e mensagens são bloqueadas

### Implementation for User Story 7

- [x] T025 [US7] Implement /mute handler in src/handlers/admin_handlers.py
- [x] T026 [US7] Add mute logic with timer

### Testing for User Story 7

- [x] T025-test [US7] Create handler tests for /mute command
- [x] T026-test [US7] Create integration tests for mute logic with timer

---

## Phase 10: User Story 8 - Admin envia broadcast (Priority: P3)

**Goal**: Permitir admin enviar mensagem para todos os membros

**Independent Test**: Admin executa /broadcast e todos recebem

### Implementation for User Story 8

- [x] T027 [US8] Implement /broadcast handler in src/handlers/admin_handlers.py
- [x] T028 [US8] Add broadcast logic to all members

### Testing for User Story 8

- [x] T027-test [US8] Create handler tests for /broadcast command
- [x] T028-test [US8] Create integration tests for broadcast to all group members

---

## Phase 11: User Story 9 - Usuário vê status (Priority: P3)

**Goal**: Permitir usuário ver status de assinatura

**Independent Test**: Usuário executa /status e vê informações

### Implementation for User Story 9

- [x] T029 [US9] Implement /status handler in src/handlers/user_handlers.py
- [x] T030 [US9] Add status display logic

### Testing for User Story 9

- [x] T029-test [US9] Create handler tests for /status command
- [x] T030-test [US9] Create integration tests for status display logic

---

## Phase 12: User Story 10 - Usuário obtém ajuda (Priority: P3)

**Goal**: Permitir usuário ver comandos disponíveis

**Independent Test**: Usuário executa /help e vê lista

### Implementation for User Story 10

- [x] T031 [US10] Implement /help handler in src/handlers/user_handlers.py
- [x] T032 [US10] Add help message logic

### Testing for User Story 10

- [x] T031-test [US10] Create handler tests for /help command
- [x] T032-test [US10] Create unit tests for help message formatting

---

## Phase 13: User Story 11 - Usuário gera link de convite (Priority: P3)

**Goal**: Permitir geração de link de convite com rastreio.

### Implementation for User Story 11

- [x] T033 [US11] Implement /invite handler in src/handlers/user_handlers.py
- [x] T034 [US11] Add invite link generation logic

### Testing for User Story 11

- [x] T033-test [US11] Create handler tests for /invite command
- [x] T034-test [US11] Create integration tests for invite link generation and tracking

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in docs/
- [X] T036 Code cleanup and refactoring
- [X] T037 Performance optimization across all stories
- [X] T038 Security hardening
- [X] T039 Run quickstart.md validation
- [X] T040 [P] Error handling for PixGo API failures in src/services/pixgo_service.py

### Testing for Polish & Cross-Cutting Concerns

- [X] T037-test [POLISH] Create performance tests for high-load scenarios
- [X] T040-test [POLISH] Create error handling tests for PixGo API failures</content>
<parameter name="filePath">/home/mau/bot/botclient/specs/001-telegram-vip-groups-bot/tasks.md