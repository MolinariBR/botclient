# Data Model Design: Bot Commands Implementation

**Date**: 2025-10-28
**Feature**: 1-bot-commands-implementation
**Status**: Complete

## Overview

Data model extensions and new entities required to support the 23 new bot commands. All changes maintain compatibility with existing schema while adding necessary fields for new functionality.

## Existing Entities (Extended)

### User Model
**File**: `src/models/user.py`

| Field | Type | Description | New/Extended |
|-------|------|-------------|--------------|
| telegram_id | String | Unique Telegram user ID | Existing |
| username | String | Telegram username | Existing |
| is_banned | Boolean | Permanent ban status | Existing |
| is_muted | Boolean | Temporary mute status | Existing |
| mute_until | DateTime | Mute expiration time | Existing |
| warn_count | Integer | Number of warnings received | **NEW** |
| auto_renew | Boolean | Auto-renewal preference | **NEW** |
| expires_at | DateTime | VIP access expiration | Existing |
| created_at | DateTime | Account creation time | Existing |
| updated_at | DateTime | Last update time | Existing |

**Relationships**:
- One-to-Many: User → Payments
- One-to-Many: User → Warnings
- Many-to-Many: User → Groups (via GroupMembership)

### Payment Model
**File**: `src/models/payment.py`

| Field | Type | Description | New/Extended |
|-------|------|-------------|--------------|
| id | Integer | Primary key | Existing |
| user_id | ForeignKey | Reference to User | Existing |
| amount | Decimal | Payment amount | Existing |
| currency | String | Currency code (BRL, USD) | Existing |
| status | Enum | Payment status | **EXTENDED** |
| payment_method | String | PIX, USDT, etc. | Existing |
| transaction_id | String | External transaction ID | Existing |
| created_at | DateTime | Payment creation time | Existing |
| completed_at | DateTime | Completion timestamp | **NEW** |

**Status Enum Values**: `pending`, `completed`, `failed`, `cancelled`, `refunded`

## New Entities

### Warning Model
**File**: `src/models/warning.py` (NEW)

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| user_id | ForeignKey | User receiving warning |
| admin_id | ForeignKey | Admin issuing warning |
| reason | Text | Warning reason/description |
| created_at | DateTime | Warning timestamp |

**Relationships**:
- Many-to-One: Warning → User (recipient)
- Many-to-One: Warning → Admin (issuer)

**Business Rules**:
- Maximum 3 warnings before automatic action
- Warnings expire after 30 days
- Admins can reset warning count

### ScheduledMessage Model
**File**: `src/models/scheduled_message.py` (NEW)

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| message | Text | Message content |
| schedule_time | Time | Daily execution time (HH:MM) |
| is_active | Boolean | Enable/disable scheduling |
| created_by | ForeignKey | Admin who created schedule |
| created_at | DateTime | Creation timestamp |

**Relationships**:
- Many-to-One: ScheduledMessage → Admin

**Business Rules**:
- Only one active schedule per time slot
- Messages sent to all registered groups
- Timezone: UTC

### SystemConfig Model
**File**: `src/models/system_config.py` (NEW)

| Field | Type | Description |
|-------|------|-------------|
| key | String | Configuration key (unique) |
| value | Text | Configuration value |
| updated_at | DateTime | Last update timestamp |
| updated_by | ForeignKey | Admin who updated |

**Relationships**:
- Many-to-One: SystemConfig → Admin

**Configuration Keys**:
- `subscription_price` - Default subscription price
- `subscription_days` - Default subscription duration
- `usdt_wallet_address` - USDT wallet for payments
- `welcome_message` - Default welcome message
- `rules_message` - Group rules text

## Entity Relationships Diagram

```
User (Extended)
├── warn_count: Integer
├── auto_renew: Boolean
├── 1:N → Payment
├── 1:N → Warning (received)
└── N:M → Group (via GroupMembership)

Admin (Existing)
├── 1:N → Warning (issued)
└── 1:N → ScheduledMessage

Payment (Extended)
├── status: Enum (extended)
└── completed_at: DateTime

Warning (NEW)
├── reason: Text
├── 1:1 → User (recipient)
└── 1:1 → Admin (issuer)

ScheduledMessage (NEW)
├── schedule_time: Time
├── 1:1 → Admin (creator)
└── 1:N → Group (broadcast target)

SystemConfig (NEW)
├── key: String (unique)
├── value: Text
└── 1:1 → Admin (updater)

Group (Existing)
└── N:M → User (via GroupMembership)
```

## Data Validation Rules

### User Model Extensions
- `warn_count`: >= 0, default 0
- `auto_renew`: Boolean, default True
- `expires_at`: Must be future date for active subscriptions

### Warning Model
- `reason`: Required, max 500 characters
- `created_at`: Auto-generated, not updatable

### ScheduledMessage Model
- `schedule_time`: Valid time format (HH:MM)
- `message`: Required, max 4000 characters (Telegram limit)
- Unique constraint on `schedule_time` when `is_active = True`

### SystemConfig Model
- `key`: Required, unique, lowercase with underscores
- `value`: Required, validated by key type
- Audit trail maintained via `updated_by` and `updated_at`

## Migration Strategy

### Phase 1: Safe Extensions
1. Add `warn_count` and `auto_renew` to User table
2. Add `completed_at` to Payment table
3. Extend Payment.status enum

### Phase 2: New Tables
1. Create Warning table
2. Create ScheduledMessage table
3. Create SystemConfig table

### Phase 3: Data Population
1. Set default values for existing records
2. Populate SystemConfig with current Config values
3. Migrate any existing scheduled content

## Indexing Strategy

### New Indexes Required
- `warning.user_id` - For user warning history
- `warning.created_at` - For warning expiration
- `scheduled_message.schedule_time` - For active schedule lookup
- `system_config.key` - For fast config lookups

### Existing Indexes Verified
- `user.telegram_id` - Already indexed
- `payment.user_id` - Already indexed
- `admin.telegram_id` - Already indexed

## Performance Considerations

### Query Patterns
- **Warning lookup**: `SELECT COUNT(*) FROM warning WHERE user_id = ? AND created_at > ?`
- **Active schedules**: `SELECT * FROM scheduled_message WHERE is_active = 1 ORDER BY schedule_time`
- **Config values**: `SELECT value FROM system_config WHERE key = ?`

### Optimization Targets
- Warning count queries: < 100ms
- Schedule checks: < 50ms
- Config lookups: < 10ms

## Backup and Recovery

### Export Scope
- All new entities included in backup
- Configuration preserved
- Warning history maintained
- Schedule settings exported

### Recovery Process
1. Restore base entities (User, Payment, Admin, Group)
2. Restore new entities in dependency order
3. Rebuild any computed fields
4. Validate schedule integrity

## Security Considerations

### Data Protection
- Warning reasons may contain sensitive information
- Config values include payment credentials
- Audit trail maintained for all changes

### Access Control
- Only admins can create/modify warnings
- Only admins can manage schedules
- Config changes logged with admin attribution

## Testing Data Strategy

### Test Fixtures
- Sample users with different warning counts
- Active and inactive schedules
- Complete system configuration set
- Edge cases: max warnings, expired schedules

### Integration Test Data
- Realistic group sizes (10-1000 members)
- Mixed payment statuses
- Concurrent admin operations</content>
<parameter name="filePath">/home/mau/bot/botclient/specs/1-bot-commands-implementation/data-model.md