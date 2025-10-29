# Tasks: Bot Commands Implementation

**Input**: Design documents from `/specs/001-bot-commands-implementation/`
**Prerequisites**: impl_plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Comprehensive unit, integration, and performance tests included for all phases and user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python project with python-telegram-bot, SQLAlchemy, requests dependencies
- [ ] T003 [P] Configure linting and formatting tools (ruff)

### Testing for Phase 1

- [ ] T001-test Create integration tests for project structure validation
- [ ] T002-test Create tests for dependency installation and imports
- [ ] T003-test [P] Create tests for linting and formatting configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup SQLite schema and SQLAlchemy models base
- [ ] T005 [P] Implement base services structure (telegram, pixgo, usdt)
- [ ] T006 [P] Setup logging infrastructure in src/utils/logger.py
- [ ] T007 Configure environment configuration management in src/utils/config.py

### Testing for Phase 2

- [ ] T004-test Create database schema tests and model validation
- [ ] T005-test [P] Create unit tests for base service initialization
- [ ] T006-test [P] Create logging system tests
- [ ] T007-test Create configuration management tests

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Admin Member Management (Priority: High) 🎯 MVP

**Goal**: Permitir admin gerenciar membros do grupo VIP (unban, unmute, userinfo, pending)

**Independent Test**: Admin executa comandos de gerenciamento e verifica mudanças no status dos usuários

### Implementation for User Story 1

- [ ] T008 [US1] Extend User model with warn_count and auto_renew fields in src/models/user.py
- [ ] T009 [US1] Extend Payment model with completed_at field in src/models/payment.py
- [ ] T010 [US1] Implement /unban handler in src/handlers/admin_handlers.py
- [ ] T011 [US1] Implement /unmute handler in src/handlers/admin_handlers.py
- [ ] T012 [US1] Implement /userinfo handler in src/handlers/admin_handlers.py
- [ ] T013 [US1] Implement /pending handler in src/handlers/admin_handlers.py

### Testing for User Story 1

- [ ] T008-test [US1] Create unit tests for User model extensions
- [ ] T009-test [US1] Create unit tests for Payment model extensions
- [ ] T010-test [US1] Create handler tests for /unban command
- [ ] T011-test [US1] Create handler tests for /unmute command
- [ ] T012-test [US1] Create handler tests for /userinfo command
- [ ] T013-test [US1] Create handler tests for /pending command

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Admin Moderation System (Priority: High)

**Goal**: Permitir admin moderar usuários com sistema de avisos e expiração manual

**Independent Test**: Admin executa comandos de moderação e verifica aplicação de regras

### Implementation for User Story 2

- [ ] T014 [US2] Create Warning model in src/models/warning.py
- [ ] T015 [US2] Implement /warn handler in src/handlers/admin_handlers.py
- [ ] T016 [US2] Implement /resetwarn handler in src/handlers/admin_handlers.py
- [ ] T017 [US2] Implement /expire handler in src/handlers/admin_handlers.py
- [ ] T018 [US2] Implement /sendto handler in src/handlers/admin_handlers.py

### Testing for User Story 2

- [ ] T014-test [US2] Create unit tests for Warning model
- [ ] T015-test [US2] Create handler tests for /warn command
- [ ] T016-test [US2] Create handler tests for /resetwarn command
- [ ] T017-test [US2] Create handler tests for /expire command
- [ ] T018-test [US2] Create handler tests for /sendto command

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: User Story 3 - Admin Configuration Management (Priority: Medium)

**Goal**: Permitir admin configurar preços, duração e carteiras

**Independent Test**: Admin executa comandos de configuração e verifica mudanças aplicadas

### Implementation for User Story 3

- [ ] T019 [US3] Create SystemConfig model in src/models/system_config.py
- [ ] T020 [US3] Implement /setprice handler in src/handlers/admin_handlers.py
- [ ] T021 [US3] Implement /settime handler in src/handlers/admin_handlers.py
- [ ] T022 [US3] Implement /setwallet handler in src/handlers/admin_handlers.py

### Testing for User Story 3

- [ ] T019-test [US3] Create unit tests for SystemConfig model
- [ ] T020-test [US3] Create handler tests for /setprice command
- [ ] T021-test [US3] Create handler tests for /settime command
- [ ] T022-test [US3] Create handler tests for /setwallet command

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Admin Content Management (Priority: Medium)

**Goal**: Permitir admin gerenciar conteúdo (regras, welcome, agendamento)

**Independent Test**: Admin configura conteúdo e verifica distribuição automática

### Implementation for User Story 4

- [ ] T023 [US4] Create ScheduledMessage model in src/models/scheduled_message.py
- [ ] T024 [US4] Implement /rules handler in src/handlers/admin_handlers.py
- [ ] T025 [US4] Implement /welcome handler in src/handlers/admin_handlers.py
- [ ] T026 [US4] Implement /schedule handler in src/handlers/admin_handlers.py

### Testing for User Story 4

- [ ] T023-test [US4] Create unit tests for ScheduledMessage model
- [ ] T024-test [US4] Create handler tests for /rules command
- [ ] T025-test [US4] Create handler tests for /welcome command
- [ ] T026-test [US4] Create handler tests for /schedule command

---

## Phase 7: User Story 5 - Admin Analytics & Monitoring (Priority: Medium)

**Goal**: Permitir admin visualizar estatísticas e logs do sistema

**Independent Test**: Admin executa comandos de análise e verifica dados corretos

### Implementation for User Story 5

- [ ] T027 [US5] Implement /stats handler in src/handlers/admin_handlers.py
- [ ] T027a [US5] Create admin action logging system in src/services/logging_service.py
- [ ] T027b [US5] Add logging decorators to all admin command handlers
- [ ] T028 [US5] Implement /logs handler in src/handlers/admin_handlers.py
- [ ] T029 [US5] Implement /admins handler in src/handlers/admin_handlers.py
- [ ] T030 [US5] Implement /settings handler in src/handlers/admin_handlers.py

### Testing for User Story 5

- [ ] T027-test [US5] Create handler tests for /stats command
- [ ] T027a-test [US5] Create unit tests for logging service
- [ ] T027b-test [US5] Create integration tests for admin action logging
- [ ] T028-test [US5] Create handler tests for /logs command
- [ ] T029-test [US5] Create handler tests for /admins command
- [ ] T030-test [US5] Create handler tests for /settings command

---

## Phase 8: User Story 6 - Admin Data Management (Priority: Low)

**Goal**: Permitir admin fazer backup e restore de dados

**Independent Test**: Admin executa backup/restore e verifica integridade dos dados

### Implementation for User Story 6

- [ ] T031 [US6] Implement /backup handler in src/handlers/admin_handlers.py
- [ ] T032 [US6] Implement /restore handler in src/handlers/admin_handlers.py

### Testing for User Story 6

- [ ] T031-test [US6] Create handler tests for /backup command
- [ ] T032-test [US6] Create handler tests for /restore command

---

## Phase 9: User Story 7 - User Account Management (Priority: Medium)

**Goal**: Permitir usuário gerenciar conta (cancelar renovação, suporte, info)

**Independent Test**: Usuário executa comandos pessoais e verifica mudanças

### Implementation for User Story 7

- [ ] T033 [US7] Implement /cancel handler in src/handlers/user_handlers.py
- [ ] T034 [US7] Implement /support handler in src/handlers/user_handlers.py
- [ ] T035 [US7] Implement /info handler in src/handlers/user_handlers.py

### Testing for User Story 7

- [ ] T033-test [US7] Create handler tests for /cancel command
- [ ] T034-test [US7] Create handler tests for /support command
- [ ] T035-test [US7] Create handler tests for /info command

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in docs/
- [ ] T037 Code cleanup and refactoring
- [ ] T038 Performance optimization across all stories
- [ ] T039 Security hardening
- [ ] T040 [P] Error handling for PixGo API failures in src/services/pixgo_service.py

### Testing for Polish & Cross-Cutting Concerns

- [ ] T036-test [POLISH] [P] Create documentation validation tests
- [ ] T037-test [POLISH] Create performance tests for high-load scenarios
- [ ] T038-test [POLISH] Create performance benchmark tests
- [ ] T039-test [POLISH] Create security audit tests
- [ ] T040-test [POLISH] Create error handling tests for PixGo API failures