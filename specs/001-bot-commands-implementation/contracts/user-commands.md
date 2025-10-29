# User Commands API Contracts

## /start

**Purpose:** Initialize user interaction with the bot.

**Input:**
- Command: `/start`
- Parameters: None

**Output:**
- Success: Welcome message with bot description and /help command suggestion
- Error: None (always succeeds)

**Database Changes:**
- Creates or updates User record with basic info

---

## /help

**Purpose:** Display available commands and usage instructions.

**Input:**
- Command: `/help`
- Parameters: None

**Output:**
- Success: Formatted help text with all available commands
- Error: None (always succeeds)

---

## /status

**Purpose:** Check user's current VIP status and payment information.

**Input:**
- Command: `/status`
- Parameters: None

**Output:**
- Success: User's current status, payment history, expiry date
- Error: "❌ Failed to retrieve status: {error_message}"

---

## /pay

**Purpose:** Initiate payment process for VIP access.

**Input:**
- Command: `/pay <amount> <currency>`
- Parameters:
  - amount: Payment amount (decimal)
  - currency: Payment currency (USD, EUR, BRL, etc.)

**Output:**
- Success: Payment instructions with payment link/button
- Error: "❌ Failed to initiate payment: {error_message}"

**Database Changes:**
- Creates Payment record with pending status

---

## /payment_history

**Purpose:** View user's payment history.

**Input:**
- Command: `/payment_history`
- Parameters: None

**Output:**
- Success: List of all payments with dates, amounts, statuses
- Error: "❌ Failed to retrieve payment history: {error_message}"

---

## /groups

**Purpose:** List all available VIP groups.

**Input:**
- Command: `/groups`
- Parameters: None

**Output:**
- Success: Formatted list of registered groups with join links
- Error: "❌ Failed to retrieve groups: {error_message}"

---

## /join

**Purpose:** Request to join a specific VIP group.

**Input:**
- Command: `/join <group_id>`
- Parameters:
  - group_id: Telegram group ID (integer)

**Output:**
- Success: "✅ Join request sent! You'll be added to the group shortly."
- Error: "❌ Failed to join group: {error_message}"
- Conditions: User must have active VIP status

**Database Changes:**
- Creates GroupMembership record with pending status

---

## /leave

**Purpose:** Leave a VIP group.

**Input:**
- Command: `/leave <group_id>`
- Parameters:
  - group_id: Telegram group ID (integer)

**Output:**
- Success: "✅ Successfully left the group"
- Error: "❌ Failed to leave group: {error_message}"

**Database Changes:**
- Removes GroupMembership record or sets as inactive

---

## /my_groups

**Purpose:** List groups the user is currently a member of.

**Input:**
- Command: `/my_groups`
- Parameters: None

**Output:**
- Success: List of user's current group memberships
- Error: "❌ Failed to retrieve groups: {error_message}"

---

## /support

**Purpose:** Get support contact information.

**Input:**
- Command: `/support`
- Parameters: None

**Output:**
- Success: Support contact info and FAQ link
- Error: None (always succeeds)

---

## /feedback

**Purpose:** Send feedback to bot administrators.

**Input:**
- Command: `/feedback <message>`
- Parameters:
  - message: Feedback text

**Output:**
- Success: "✅ Thank you for your feedback!"
- Error: "❌ Failed to send feedback: {error_message}"

**Database Changes:**
- Creates Feedback record

---

## /report

**Purpose:** Report a user or issue in a group.

**Input:**
- Command: `/report <user_id> <reason>`
- Parameters:
  - user_id: Telegram user ID to report (integer)
  - reason: Report reason text

**Output:**
- Success: "✅ Report submitted successfully"
- Error: "❌ Failed to submit report: {error_message}"

**Database Changes:**
- Creates Report record for admin review

---

## /profile

**Purpose:** View and edit user profile information.

**Input:**
- Command: `/profile`
- Parameters: None

**Output:**
- Success: User's profile information with edit options
- Error: "❌ Failed to retrieve profile: {error_message}"

---

## /settings

**Purpose:** Manage user notification and privacy settings.

**Input:**
- Command: `/settings`
- Parameters: None

**Output:**
- Success: Current settings with toggle options
- Error: "❌ Failed to retrieve settings: {error_message}"

**Database Changes:**
- Updates UserSettings record

---

## /invite

**Purpose:** Generate invitation link for new users.

**Input:**
- Command: `/invite`
- Parameters: None

**Output:**
- Success: Invitation link with referral code
- Error: "❌ Failed to generate invite: {error_message}"
- Conditions: User must have active VIP status

**Database Changes:**
- Creates Invitation record with unique code

---

## /leaderboard

**Purpose:** View top users by various metrics.

**Input:**
- Command: `/leaderboard <type>`
- Parameters:
  - type: Optional leaderboard type (payments, referrals, activity)

**Output:**
- Success: Formatted leaderboard with rankings
- Error: "❌ Failed to retrieve leaderboard: {error_message}"