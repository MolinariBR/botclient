import json
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock

import pytest

from src.services.logging_service import LoggingService


class TestLoggingService:
    """Test cases for LoggingService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_admin_actions.log")

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_creates_log_directory(self):
        """Test that __init__ creates the log directory if it doesn't exist"""
        nested_dir = os.path.join(self.temp_dir, "nested", "logs")
        log_file = os.path.join(nested_dir, "admin_actions.log")

        logging_service = LoggingService(log_file)

        assert os.path.exists(nested_dir)
        assert logging_service.log_file == log_file

        # Cleanup - remove the nested directory structure
        import shutil
        shutil.rmtree(os.path.join(self.temp_dir, "nested"))

    def test_log_admin_action_success(self):
        """Test logging a successful admin action"""
        logging_service = LoggingService(self.log_file)

        with patch('src.services.logging_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"

            logging_service.log_admin_action(
                admin_id=12345,
                action="ban_user",
                target_user_id=67890,
                target_group_id=-1001234567890,
                details={"reason": "spam"},
                success=True
            )

        # Verify log file was created and contains correct data
        assert os.path.exists(self.log_file)

        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1

            log_entry = json.loads(lines[0].strip())
            assert log_entry["timestamp"] == "2023-01-01T12:00:00"
            assert log_entry["admin_id"] == 12345
            assert log_entry["action"] == "ban_user"
            assert log_entry["target_user_id"] == 67890
            assert log_entry["target_group_id"] == -1001234567890
            assert log_entry["details"] == {"reason": "spam"}
            assert log_entry["success"] is True

    def test_log_admin_action_failure(self):
        """Test logging a failed admin action"""
        logging_service = LoggingService(self.log_file)

        with patch('src.services.logging_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"

            logging_service.log_admin_action(
                admin_id=12345,
                action="ban_user",
                target_user_id=67890,
                success=False,
                details={"error": "User not found"}
            )

        # Verify log file contains failure data
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            log_entry = json.loads(lines[0].strip())
            assert log_entry["success"] is False
            assert log_entry["details"] == {"error": "User not found"}

    def test_log_admin_action_file_write_error(self):
        """Test handling of file write errors"""
        logging_service = LoggingService(self.log_file)

        with patch('builtins.open', side_effect=Exception("Disk full")), \
             patch('src.services.logging_service.logger') as mock_logger:

            logging_service.log_admin_action(
                admin_id=12345,
                action="test_action"
            )

            mock_logger.error.assert_called_once_with("Failed to write admin action log: Disk full")

    def test_get_recent_logs_empty_file(self):
        """Test getting recent logs from empty file"""
        logging_service = LoggingService(self.log_file)

        logs = logging_service.get_recent_logs()

        assert logs == []

    def test_get_recent_logs_with_data(self):
        """Test getting recent logs with data"""
        logging_service = LoggingService(self.log_file)

        # Create some test log entries
        test_logs = [
            {"timestamp": "2023-01-01T10:00:00", "admin_id": 1, "action": "action1"},
            {"timestamp": "2023-01-01T11:00:00", "admin_id": 2, "action": "action2"},
            {"timestamp": "2023-01-01T12:00:00", "admin_id": 3, "action": "action3"},
        ]

        with open(self.log_file, 'w', encoding='utf-8') as f:
            for log in test_logs:
                f.write(json.dumps(log) + '\n')

        logs = logging_service.get_recent_logs(limit=2)

        assert len(logs) == 2
        assert logs[0]["admin_id"] == 2  # Should get last 2 entries
        assert logs[1]["admin_id"] == 3

    def test_get_recent_logs_with_level_filter(self):
        """Test getting recent logs with level filtering"""
        logging_service = LoggingService(self.log_file)

        test_logs = [
            {"timestamp": "2023-01-01T10:00:00", "admin_id": 1, "action": "action1", "level": "INFO"},
            {"timestamp": "2023-01-01T11:00:00", "admin_id": 2, "action": "action2", "level": "ERROR"},
        ]

        with open(self.log_file, 'w', encoding='utf-8') as f:
            for log in test_logs:
                f.write(json.dumps(log) + '\n')

        logs = logging_service.get_recent_logs(level="ERROR")

        assert len(logs) == 1
        assert logs[0]["level"] == "ERROR"

    def test_get_recent_logs_invalid_json(self):
        """Test handling of invalid JSON in log file"""
        logging_service = LoggingService(self.log_file)

        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("invalid json line\n")
            f.write('{"valid": "json"}\n')

        logs = logging_service.get_recent_logs()

        assert len(logs) == 1
        assert logs[0]["valid"] == "json"

    def test_get_recent_logs_file_read_error(self):
        """Test handling of file read errors"""
        logging_service = LoggingService(self.log_file)

        # Create the file so os.path.exists returns True
        with open(self.log_file, 'w') as f:
            f.write("dummy")

        with patch('builtins.open', side_effect=Exception("Permission denied")), \
             patch('src.services.logging_service.logger') as mock_logger:

            logs = logging_service.get_recent_logs()

            assert logs == []
            mock_logger.error.assert_called_once_with("Failed to read logs: Permission denied")

    @patch('src.services.logging_service.datetime')
    def test_create_admin_action_decorator_success(self, mock_datetime):
        """Test the admin action decorator for successful actions"""
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        logging_service = LoggingService(self.log_file)

        # Create a mock handler function
        mock_handler = AsyncMock()
        mock_handler.return_value = "success_result"

        # Create decorated function
        decorator = LoggingService.create_admin_action_decorator(logging_service, "test_action")
        decorated_handler = decorator(mock_handler)

        # Create mock update and context
        mock_update = Mock()
        mock_user = Mock()
        mock_user.id = 12345
        mock_update.effective_user = mock_user
        mock_update.effective_chat = None

        mock_context = Mock()
        mock_context.args = ["67890"]  # target user ID

        # Execute decorated function
        import asyncio
        result = asyncio.run(decorated_handler(mock_update, mock_context))

        # Verify handler was called
        assert result == "success_result"
        mock_handler.assert_called_once_with(mock_update, mock_context)

        # Verify log was written
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1

            log_entry = json.loads(lines[0].strip())
            assert log_entry["admin_id"] == 12345
            assert log_entry["action"] == "test_action"
            assert log_entry["target_user_id"] == 67890
            assert log_entry["success"] is True

    @patch('src.services.logging_service.datetime')
    def test_create_admin_action_decorator_failure(self, mock_datetime):
        """Test the admin action decorator for failed actions"""
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        logging_service = LoggingService(self.log_file)

        # Create a mock handler that raises exception
        mock_handler = AsyncMock()
        mock_handler.side_effect = Exception("Handler failed")

        # Create decorated function
        decorator = LoggingService.create_admin_action_decorator(logging_service, "test_action")
        decorated_handler = decorator(mock_handler)

        # Create mock update and context
        mock_update = Mock()
        mock_user = Mock()
        mock_user.id = 12345
        mock_update.effective_user = mock_user
        mock_update.effective_chat = None

        mock_context = Mock()
        mock_context.args = None

        # Execute decorated function (should not raise)
        import asyncio
        with pytest.raises(Exception, match="Handler failed"):
            asyncio.run(decorated_handler(mock_update, mock_context))

        # Verify log was written with failure
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1

            log_entry = json.loads(lines[0].strip())
            assert log_entry["success"] is False
            assert log_entry["details"]["error"] == "Handler failed"

    def test_create_admin_action_decorator_no_user(self):
        """Test decorator when no user is present"""
        logging_service = LoggingService(self.log_file)

        mock_handler = AsyncMock()
        mock_handler.return_value = "result"

        decorator = LoggingService.create_admin_action_decorator(logging_service, "test_action")
        decorated_handler = decorator(mock_handler)

        mock_update = Mock()
        mock_update.effective_user = None
        mock_context = Mock()

        import asyncio
        result = asyncio.run(decorated_handler(mock_update, mock_context))

        assert result == "result"
        # Should not create any log files
        assert not os.path.exists(self.log_file) or os.path.getsize(self.log_file) == 0

    def test_create_admin_action_decorator_group_chat(self):
        """Test decorator extracts group ID from group chats"""
        logging_service = LoggingService(self.log_file)

        mock_handler = AsyncMock()
        mock_handler.return_value = "result"

        decorator = LoggingService.create_admin_action_decorator(logging_service, "test_action")
        decorated_handler = decorator(mock_handler)

        mock_update = Mock()
        mock_user = Mock()
        mock_user.id = 12345
        mock_update.effective_user = mock_user

        mock_chat = Mock()
        mock_chat.type = "group"
        mock_chat.id = -1001234567890
        mock_update.effective_chat = mock_chat

        mock_context = Mock()
        mock_context.args = None

        import asyncio
        asyncio.run(decorated_handler(mock_update, mock_context))

        # Verify group ID was logged
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.read().strip())
            assert log_entry["target_group_id"] == -1001234567890