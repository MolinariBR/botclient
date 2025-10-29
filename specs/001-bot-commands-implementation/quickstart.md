# Bot Commands Implementation - Quick Start

## Overview

This implementation adds 23 missing bot commands to complete the Telegram VIP Groups Bot functionality. The commands are organized into three categories: Admin, User, and System commands.

## Prerequisites

- Python 3.11+
- python-telegram-bot library
- SQLAlchemy ORM
- SQLite database
- Bot token from @BotFather

## Quick Setup

1. **Install Dependencies:**
   ```bash
   pip install python-telegram-bot sqlalchemy requests
   ```

2. **Configure Environment:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export DATABASE_URL="sqlite:///bot.db"
   ```

3. **Initialize Database:**
   ```python
   from src.database import init_db
   init_db()
   ```

4. **Start Bot:**
   ```bash
   python src/main.py
   ```

## Command Categories

### Admin Commands (13 commands)
- `/register_group` - Register groups as VIP
- `/group_id` - Get group ID for registration
- `/add_admin` / `/remove_admin` - Admin management
- `/list_admins` - View all admins
- `/stats` - System statistics
- `/broadcast` - Send messages to all groups
- `/warn_user` / `/user_warnings` / `/clear_warnings` - User moderation
- `/ban_user` / `/unban_user` / `/list_bans` - User banning system

### User Commands (10 commands)
- `/start` / `/help` - Basic bot interaction
- `/status` - Check VIP status
- `/pay` / `/payment_history` - Payment system
- `/groups` / `/join` / `/leave` / `/my_groups` - Group management
- `/support` / `/feedback` / `/report` - Support system
- `/profile` / `/settings` - User preferences
- `/invite` / `/leaderboard` - Social features

### System Commands (13 commands)
- `/schedule_message` / `/list_scheduled` / `/cancel_scheduled` - Message scheduling
- `/system_config` - Configuration management
- `/backup` / `/maintenance` - System maintenance
- `/logs` / `/health_check` - Monitoring
- `/restart` / `/shutdown` - Service control
- `/version` - Version information
- `/export_data` / `/import_data` - Data management

## Key Features

### Security & Permissions
- Admin-only commands are protected with permission checks
- User commands validate VIP status where required
- All database operations include proper error handling

### Database Integration
- All commands integrate with SQLAlchemy models
- Automatic transaction handling
- Audit trails for admin actions

### Error Handling
- Consistent error messages across all commands
- Graceful failure handling
- User-friendly feedback

## Development Workflow

1. **Design Phase** ✅ Complete
   - Data models designed
   - API contracts specified
   - Implementation plan created

2. **Implementation Phase** 🔄 In Progress
   - Handler methods to be implemented
   - Database migrations to be applied
   - Integration tests to be written

3. **Testing Phase** 📋 Planned
   - Unit tests for each command
   - Integration tests for workflows
   - End-to-end testing

## File Structure

```
src/
├── handlers/
│   ├── admin_handlers.py    # Admin command handlers
│   ├── user_handlers.py     # User command handlers
│   └── system_handlers.py   # System command handlers (new)
├── models/
│   ├── user.py
│   ├── payment.py
│   ├── group.py
│   ├── admin.py
│   ├── warning.py           # New model
│   ├── ban.py              # New model
│   ├── scheduled_message.py # New model
│   └── system_config.py    # New model
├── services/
│   ├── telegram_service.py
│   ├── payment_service.py
│   └── moderation_service.py # New service
└── utils/
    ├── validators.py
    └── formatters.py
```

## Next Steps

1. Implement handler methods for each command
2. Add new database models and migrations
3. Create service layer methods
4. Add comprehensive error handling
5. Write unit and integration tests
6. Update help command with new commands

## Support

For questions about specific commands, refer to the detailed API contracts in the `contracts/` directory.