# Feature Specification: Bot Commands Implementation

**Feature ID**: 001-bot-commands-implementation
**Created**: 2025-10-28
**Status**: Specification Complete
**Priority**: High

## Overview

Implement all missing bot commands as specified in `commands.md` and `implementation_plan.md` to provide complete administrative and user functionality for the Telegram VIP bot.

## User Scenarios & Testing

### Primary User Scenarios

#### Admin User - Managing Members
1. **Unban User**: Admin types `/unban @username` in private chat, bot removes ban and confirms action
2. **Unmute User**: Admin types `/unmute @username`, bot removes mute and confirms
3. **View User Info**: Admin types `/userinfo @username`, bot displays comprehensive user details
4. **Check Pending Payments**: Admin types `/pending`, bot lists all users with pending payments

#### Admin User - Moderation System
5. **Warn User**: Admin types `/warn @username spamming`, bot sends warning and increments strike count
6. **Reset Warnings**: Admin types `/resetwarn @username`, bot clears all warnings for user
7. **Expire Access**: Admin types `/expire @username`, bot immediately expires user's VIP access

#### Admin User - Communication
8. **Send Private Message**: Admin types `/sendto @username hello there`, bot forwards message to user privately

#### Admin User - Configuration
9. **Set Subscription Price**: Admin types `/setprice 50 BRL`, bot updates price and confirms
10. **Set Subscription Duration**: Admin types `/settime 30`, bot updates to 30 days
11. **Set Wallet Address**: Admin types `/setwallet 0x123...`, bot updates USDT wallet

#### Admin User - Content Management
12. **Send Rules**: Admin types `/rules`, bot sends predefined rules message
13. **Set Welcome Message**: Admin types `/welcome Welcome to VIP!`, bot saves for new members
14. **Schedule Message**: Admin types `/schedule 09:00 Good morning VIPs!`, bot schedules daily message

#### Admin User - Analytics & Monitoring
15. **View Statistics**: Admin types `/stats`, bot shows member counts, growth metrics, engagement
16. **View Action Logs**: Admin types `/logs`, bot shows recent admin actions and user activities
17. **List Admins**: Admin types `/admins`, bot lists all bot administrators
18. **Settings Panel**: Admin types `/settings`, bot shows interactive configuration menu

#### Admin User - Data Management
19. **Create Backup**: Admin types `/backup`, bot generates and sends data export file
20. **Restore Backup**: Admin types `/restore`, bot processes uploaded backup file

#### Regular User - Account Management
21. **Cancel Auto-Renewal**: User types `/cancel`, bot disables automatic subscription renewal
22. **Get Support**: User types `/support`, bot provides contact information or forwards to admin
23. **View Group Info**: User types `/info`, bot shows details about the VIP group/mentorship

### Edge Cases & Error Scenarios

- Command used by non-admin user → "Access denied" message
- Invalid username provided → "User not found" message
- User already unbanned/unmuted → "User is not banned/muted" message
- Empty message for broadcast/sendto → "Message cannot be empty" error
- Invalid time format for schedule → "Invalid time format" error
- Backup file too large → "File size exceeds limit" error
- No pending payments → "No pending payments found" message

## Functional Requirements

### Core Administration (Priority: High)
1. **Unban Command**: System must allow admins to remove permanent bans from users
2. **Unmute Command**: System must allow admins to remove temporary mutes from users
3. **User Info Display**: System must show comprehensive user information including:
   - Telegram ID and username
   - VIP status (active/expired/pending)
   - Subscription expiry date
   - Payment history (last 5 payments)
   - Warning count and mute status
   - Join date and auto-renewal setting
4. **Pending Payments List**: System must display all users with outstanding payments

### Moderation System (Priority: High)
5. **Warning System**: System must track and increment warning strikes for users
6. **Warning Reset**: System must allow clearing of all warnings for a user
7. **Manual Expiration**: System must allow immediate expiration of user access
8. **Private Messaging**: System must enable admins to send private messages to individual users

### Configuration Management (Priority: Medium)
9. **Price Configuration**: System must allow updating subscription prices
10. **Duration Configuration**: System must allow updating subscription durations
11. **Wallet Configuration**: System must allow updating cryptocurrency wallet addresses
12. **USDT Polygon Configuration**: System must support fixed USDT Polygon wallet address for alternative payments

### Content Management (Priority: Medium)
13. **Rules Distribution**: System must store and distribute group rules
14. **Welcome Messages**: System must configure and automatically send welcome messages to new members
15. **Message Scheduling**: System must support scheduling recurring messages

### Analytics & Monitoring (Priority: Medium)
16. **Statistics Dashboard**: System must provide member statistics including:
    - Total active users
    - New users this month
    - Total payments processed
    - Average payment value
    - User retention rate (30-day)
    - Command usage statistics
17. **Action Logging**: System must log and display administrative actions
18. **Admin Management**: System must list all bot administrators
19. **Settings Interface**: System must provide interactive configuration options

### Data Management (Priority: Low)
20. **Data Backup**: System must export all user and configuration data
21. **Data Restore**: System must import and validate backup data

### User Features (Priority: Medium)
22. **Auto-Renewal Cancellation**: System must allow users to disable automatic renewals
23. **Support Access**: System must provide support contact methods
24. **Group Information**: System must display group details and mentorship information

## Success Criteria

### Functional Completeness
- All 23 commands from `commands.md` are implemented and functional
- Commands work correctly in both private and group chats (as appropriate)
- Error handling provides clear, actionable feedback to users

### User Experience
- Commands respond within 3 seconds under normal load
- Help system includes all new commands with clear descriptions
- Admin commands are properly restricted to authorized users only

### System Reliability
- No command causes system crashes or data corruption
- All database operations complete successfully or rollback on failure
- Logging captures all administrative actions for audit purposes

### Performance
- System handles 100 concurrent users without performance degradation
- Database queries complete within 1 second for user-facing operations
- Scheduled tasks execute at correct times with 99% reliability

## Key Entities

### User
- telegram_id (string, unique)
- username (string)
- is_banned (boolean)
- is_muted (boolean)
- mute_until (datetime)
- warn_count (integer)
- auto_renew (boolean)
- expires_at (datetime)
- created_at (datetime)
- updated_at (datetime)

### Payment
- id (integer, primary key)
- user_id (foreign key)
- amount (decimal)
- currency (string)
- status (enum: pending, completed, failed, cancelled)
- payment_method (string)
- transaction_id (string)
- created_at (datetime)
- completed_at (datetime)

### Admin
- telegram_id (string, unique)
- created_at (datetime)

### Group
- telegram_group_id (string, unique)
- name (string)
- created_at (datetime)

### GroupMembership
- user_id (foreign key)
- group_id (foreign key)
- joined_at (datetime)

### Warning (new entity)
- id (integer, primary key)
- user_id (foreign key)
- admin_id (foreign key)
- reason (text)
- created_at (datetime)

### ScheduledMessage (new entity)
- id (integer, primary key)
- message (text)
- schedule_time (time)
- is_active (boolean)
- created_by (foreign key)
- created_at (datetime)

### SystemConfig (new entity)
- key (string, unique)
- value (text)
- updated_at (datetime)
- updated_by (foreign key)

## Assumptions

1. **Database Schema**: Existing models (User, Payment, Admin, Group) are stable and won't change during implementation
2. **Permissions**: Admin status is determined by presence in Admin table
3. **Chat Types**: Private chat commands work in private chats only, group commands work in groups
4. **Data Validation**: User input validation follows existing patterns in the codebase
5. **Error Handling**: Follow existing error handling patterns with user-friendly messages
6. **Performance**: Implementation won't significantly impact existing bot performance
7. **Backup Format**: JSON format for data export/import operations
8. **Time Zones**: All times stored in UTC, displayed in user's local time when possible
9. **File Limits**: Backup files limited to reasonable sizes (under 10MB)
10. **Rate Limiting**: No additional rate limiting needed beyond existing protections

## Dependencies

- Python Telegram Bot library (already installed)
- SQLAlchemy ORM (already configured)
- Existing database models and session management
- Logging system (already implemented)
- Performance monitoring (already implemented)

## Risks & Mitigations

### High Risk
- **Data Corruption**: Database changes could corrupt existing data
  - Mitigation: Comprehensive testing with backup/restore before deployment

### Medium Risk
- **Performance Impact**: New queries could slow down existing operations
  - Mitigation: Query optimization and performance testing

### Low Risk
- **Command Conflicts**: New commands might conflict with existing ones
  - Mitigation: Code review ensures unique command names

## Testing Strategy

### Unit Tests
- Individual command handlers with mocked dependencies
- Database operations with test data
- Error condition handling

### Integration Tests
- Full command flows with real database
- Multi-user scenarios
- Scheduled task execution

### User Acceptance Tests
- Admin users test all commands in staging environment
- Regular users test new features
- Performance testing under load</content>
<parameter name="filePath">/home/mau/bot/botclient/specs/1-bot-commands-implementation/spec.md