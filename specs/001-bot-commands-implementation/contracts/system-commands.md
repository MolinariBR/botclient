# System Commands API Contracts

## /schedule_message

**Purpose:** Schedule a message to be sent at a specific time.

**Input:**
- Command: `/schedule_message <group_id> <datetime> <message>`
- Parameters:
  - group_id: Target group ID (integer)
  - datetime: ISO format datetime string (YYYY-MM-DD HH:MM:SS)
  - message: Message content to send

**Output:**
- Success: "✅ Message scheduled for {datetime}"
- Error: "❌ Failed to schedule message: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Creates ScheduledMessage record

---

## /list_scheduled

**Purpose:** List all scheduled messages.

**Input:**
- Command: `/list_scheduled`
- Parameters: None

**Output:**
- Success: List of scheduled messages with IDs, times, and content preview
- Error: "❌ Failed to retrieve scheduled messages: {error_message}"
- Conditions: Only admins can execute

---

## /cancel_scheduled

**Purpose:** Cancel a scheduled message.

**Input:**
- Command: `/cancel_scheduled <message_id>`
- Parameters:
  - message_id: Scheduled message ID (integer)

**Output:**
- Success: "✅ Scheduled message cancelled"
- Error: "❌ Failed to cancel message: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Deletes or deactivates ScheduledMessage record

---

## /system_config

**Purpose:** View or update system configuration.

**Input:**
- Command: `/system_config [key] [value]`
- Parameters:
  - key: Optional configuration key to view/update
  - value: Optional new value for the key

**Output:**
- Success: Current config or confirmation of update
- Error: "❌ Failed to access system config: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Updates SystemConfig records

---

## /backup

**Purpose:** Create a database backup.

**Input:**
- Command: `/backup`
- Parameters: None

**Output:**
- Success: "✅ Backup created successfully: {backup_path}"
- Error: "❌ Failed to create backup: {error_message}"
- Conditions: Only admins can execute

---

## /maintenance

**Purpose:** Run maintenance tasks (cleanup old data, optimize database).

**Input:**
- Command: `/maintenance`
- Parameters: None

**Output:**
- Success: "✅ Maintenance completed successfully"
- Error: "❌ Maintenance failed: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Various cleanup operations on expired records

---

## /logs

**Purpose:** View recent system logs.

**Input:**
- Command: `/logs [level] [limit]`
- Parameters:
  - level: Optional log level filter (INFO, WARNING, ERROR)
  - limit: Optional number of log entries (default 50)

**Output:**
- Success: Formatted log entries
- Error: "❌ Failed to retrieve logs: {error_message}"
- Conditions: Only admins can execute

---

## /health_check

**Purpose:** Run system health diagnostics.

**Input:**
- Command: `/health_check`
- Parameters: None

**Output:**
- Success: System health status report
- Error: "❌ Health check failed: {error_message}"
- Conditions: Only admins can execute

---

## /restart

**Purpose:** Restart the bot service.

**Input:**
- Command: `/restart`
- Parameters: None

**Output:**
- Success: "✅ Bot restarting..."
- Error: "❌ Failed to restart bot: {error_message}"
- Conditions: Only admins can execute

---

## /shutdown

**Purpose:** Shutdown the bot service.

**Input:**
- Command: `/shutdown`
- Parameters: None

**Output:**
- Success: "✅ Bot shutting down..."
- Error: "❌ Failed to shutdown bot: {error_message}"
- Conditions: Only admins can execute

---

## /version

**Purpose:** Get bot version and system information.

**Input:**
- Command: `/version`
- Parameters: None

**Output:**
- Success: Version info, uptime, system stats
- Error: None (always succeeds)

---

## /export_data

**Purpose:** Export system data to CSV/JSON.

**Input:**
- Command: `/export_data <table> [format]`
- Parameters:
  - table: Database table to export (users, payments, groups, etc.)
  - format: Optional export format (csv, json - default csv)

**Output:**
- Success: "✅ Data exported to {file_path}"
- Error: "❌ Failed to export data: {error_message}"
- Conditions: Only admins can execute

---

## /import_data

**Purpose:** Import data from CSV/JSON file.

**Input:**
- Command: `/import_data <table> <file_path>`
- Parameters:
  - table: Target database table
  - file_path: Path to import file

**Output:**
- Success: "✅ Data imported successfully: {records_count} records"
- Error: "❌ Failed to import data: {error_message}"
- Conditions: Only admins can execute

**Database Changes:**
- Inserts records into specified table