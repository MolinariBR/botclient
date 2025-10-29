# Admin Commands API Contracts

## /register_group

**Purpose:** Register a Telegram group as a VIP group in the system.

**Input:**
- Command: `/register_group`
- Parameters: None (group ID extracted from message context)
- Context: Must be sent in a group chat

**Output:**
- Success: "✅ Group registered successfully! Group ID: {group_id}"
- Error: "❌ Failed to register group: {error_message}"
- Conditions: Only admins can execute, group not already registered

**Database Changes:**
- Creates new Group record with group_id, title, registration_date
- Links group to registering admin

---

## /group_id

**Purpose:** Get the current group's ID for registration purposes.

**Input:**
- Command: `/group_id`
- Parameters: None
- Context: Must be sent in a group chat

**Output:**
- Success: "📋 Group ID: `{group_id}`\n\nUse this ID to register the group with /register_group"
- Error: "❌ This command must be used in a group chat"

---

## /add_admin

**Purpose:** Add a new admin to the bot system.

**Input:**
- Command: `/add_admin <user_id>`
- Parameters:
  - user_id: Telegram user ID (integer)

**Output:**
- Success: "✅ Admin added successfully! User ID: {user_id}"
- Error: "❌ Failed to add admin: {error_message}"
- Conditions: Only existing admins can execute, user_id must be valid

**Database Changes:**
- Creates new Admin record with user_id, added_by, added_date

---

## /remove_admin

**Purpose:** Remove an admin from the bot system.

**Input:**
- Command: `/remove_admin <user_id>`
- Parameters:
  - user_id: Telegram user ID (integer)

**Output:**
- Success: "✅ Admin removed successfully! User ID: {user_id}"
- Error: "❌ Failed to remove admin: {error_message}"
- Conditions: Only existing admins can execute, cannot remove self

**Database Changes:**
- Soft deletes Admin record (sets is_active = false)

---

## /list_admins

**Purpose:** List all active admins in the system.

**Input:**
- Command: `/list_admins`
- Parameters: None

**Output:**
- Success: Formatted list of admins with IDs and names
- Error: "❌ Failed to retrieve admin list: {error_message}"
- Conditions: Only admins can execute

---

## /stats

**Purpose:** Get system statistics.

**Input:**
- Command: `/stats`
- Parameters: None

**Output:**
- Success: Formatted statistics including user count, group count, payment totals
- Error: "❌ Failed to retrieve statistics: {error_message}"
- Conditions: Only admins can execute

---

## /broadcast

**Purpose:** Send a message to all registered groups.

**Input:**
- Command: `/broadcast <message>`
- Parameters:
  - message: Text to broadcast (can include newlines with \n)

**Output:**
- Success: "✅ Message broadcasted to {count} groups"
- Error: "❌ Failed to broadcast: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Creates Broadcast record for audit trail

---

## /warn_user

**Purpose:** Issue a warning to a user.

**Input:**
- Command: `/warn_user <user_id> <reason>`
- Parameters:
  - user_id: Telegram user ID (integer)
  - reason: Warning reason text

**Output:**
- Success: "✅ Warning issued to user {user_id}"
- Error: "❌ Failed to warn user: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Creates Warning record with user_id, reason, issued_by, issued_date

---

## /user_warnings

**Purpose:** Check warnings for a specific user.

**Input:**
- Command: `/user_warnings <user_id>`
- Parameters:
  - user_id: Telegram user ID (integer)

**Output:**
- Success: List of warnings with dates and reasons
- Error: "❌ Failed to retrieve warnings: {error_message}"
- Conditions: Only admins can execute

---

## /clear_warnings

**Purpose:** Clear all warnings for a user.

**Input:**
- Command: `/clear_warnings <user_id>`
- Parameters:
  - user_id: Telegram user ID (integer)

**Output:**
- Success: "✅ Warnings cleared for user {user_id}"
- Error: "❌ Failed to clear warnings: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Sets all Warning records for user as resolved

---

## /ban_user

**Purpose:** Ban a user from all VIP groups.

**Input:**
- Command: `/ban_user <user_id> <reason>`
- Parameters:
  - user_id: Telegram user ID (integer)
  - reason: Ban reason text

**Output:**
- Success: "✅ User {user_id} banned from all groups"
- Error: "❌ Failed to ban user: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Creates Ban record, removes user from all groups

---

## /unban_user

**Purpose:** Unban a user from all VIP groups.

**Input:**
- Command: `/unban_user <user_id>`
- Parameters:
  - user_id: Telegram user ID (integer)

**Output:**
- Success: "✅ User {user_id} unbanned"
- Error: "❌ Failed to unban user: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Removes active Ban record for user

---

## /list_bans

**Purpose:** List all currently banned users.

**Input:**
- Command: `/list_bans`
- Parameters: None

**Output:**
- Success: Formatted list of banned users with reasons and dates
- Error: "❌ Failed to retrieve ban list: {error_message}"
- Conditions: Only admins can execute