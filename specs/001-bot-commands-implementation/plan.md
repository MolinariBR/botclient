# Implementation Plan: Bot Commands Implementation

**Branch**: `001-bot-commands-implementation` | **Date**: 2025-10-28 | **Spec**: specs/001-bot-commands-implementation/spec.md
**Input**: Feature specification from `specs/1-bot-commands-implementation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement all 23 missing bot commands from commands.md to provide complete administrative and user functionality for the Telegram VIP bot. The implementation will extend existing Python/Telegram bot architecture with new command handlers, database models, and configuration systems.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: python-telegram-bot==20.7, SQLAlchemy==2.0.23, requests==2.31.0, psutil==5.9.6  
**Storage**: SQLite with SQLAlchemy ORM (single file database for simplicity)  
**Testing**: pytest==7.4.3 with existing test structure  
**Target Platform**: Linux server (Ubuntu 20.04+)  
**Project Type**: Single project (existing Telegram bot)  
**Performance Goals**: Handle 100 concurrent users, command responses within 3 seconds (measured from command receipt to user feedback)  
**Constraints**: Secure payment processing via PIXGO API with encrypted keys, admin-only access control via database roles, comprehensive error handling with user-friendly messages  
**Scale/Scope**: 1000+ users, 23 new commands, maintain existing bot stability

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ Plano deve incluir medidas de segurança para processamento de pagamentos via PIXGO.
- ✅ Implementar controle de acesso baseado em administradores e usuários comuns.
- ✅ Integrar com APIs externas de forma testada e monitorada.
- ✅ Incluir sistema de logs para ações do bot.
- ✅ Garantir simplicidade e escalabilidade no design.

**Status**: PASSED - All constitution requirements addressed in specification and will be maintained in implementation.

## Project Structure

### Documentation (this feature)

```text
specs/1-bot-commands-implementation/
├── impl_plan.md         # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── handlers/
│   ├── admin_handlers.py    # Extend with 20 new admin commands
│   └── user_handlers.py     # Extend with 3 new user commands
├── models/
│   ├── user.py              # Add warn_count, auto_renew fields
│   ├── payment.py           # Status field for pending tracking
│   ├── warning.py           # NEW: Warning tracking entity
│   ├── scheduled_message.py # NEW: Message scheduling entity
│   └── system_config.py     # NEW: Configuration storage entity
├── services/
│   ├── telegram_service.py  # Extend with new message methods
│   ├── mute_service.py      # Existing - ensure compatibility
│   ├── pixgo_service.py     # Existing - ensure compatibility
│   └── usdt_service.py      # Existing - ensure compatibility
└── utils/
    ├── config.py            # Extend with new configuration options
    ├── logger.py            # Existing logging system
    └── performance.py       # Existing monitoring

tests/
├── unit/
│   └── test_commands.py     # NEW: Unit tests for new commands
├── integration/
│   └── test_bot_flows.py    # NEW: Integration tests for command flows
└── contract/
    └── test_apis.py         # NEW: API contract tests
```

**Structure Decision**: Extended existing single-project structure. New commands integrated into existing handlers, new models added to models directory, tests follow existing pytest structure. Maintains separation of concerns with services layer.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations - implementation follows existing patterns and maintains simplicity.*
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
