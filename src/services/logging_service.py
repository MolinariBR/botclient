import json
import logging
import os
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LoggingService:
    """Service for logging admin actions and system events"""

    def __init__(self, log_file: str = "logs/admin_actions.log"):
        self.log_file = log_file
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        """Ensure the log directory exists"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def log_admin_action(
        self,
        admin_id: int,
        action: str,
        target_user_id: Optional[int] = None,
        target_group_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """Log an admin action"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "admin_id": admin_id,
            "action": action,
            "target_user_id": target_user_id,
            "target_group_id": target_group_id,
            "details": details or {},
            "success": success
        }

        # Write to file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write admin action log: {e}")

        # Also log to standard logger
        log_level = logging.INFO if success else logging.WARNING
        logger.log(log_level, f"Admin action: {action}", extra=log_entry)

    def get_recent_logs(self, limit: int = 50, level: Optional[str] = None) -> list:
        """Get recent log entries"""
        try:
            if not os.path.exists(self.log_file):
                return []

            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-limit:]  # Get last N lines

            logs = []
            for line in lines:
                try:
                    log_entry = json.loads(line.strip())
                    if level and log_entry.get('level') != level:
                        continue
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    continue

            return logs
        except Exception as e:
            logger.error(f"Failed to read logs: {e}")
            return []

    def log_admin_action_decorator(self, action_name: str):
        """Decorator to automatically log admin actions"""
        def decorator(func):
            @wraps(func)
            async def wrapper(update, context, *args, **kwargs):
                # Extract admin info
                user = update.effective_user
                if not user:
                    return await func(update, context, *args, **kwargs)

                admin_id = user.id

                # Extract target info from context args if available
                target_user_id = None
                target_group_id = None

                if context.args:
                    # Try to parse first arg as user ID
                    try:
                        target_user_id = int(context.args[0])
                    except (ValueError, IndexError):
                        pass

                # Extract group ID from chat if it's a group
                chat = update.effective_chat
                if chat and chat.type in ['group', 'supergroup']:
                    target_group_id = chat.id

                # Call the function
                try:
                    result = await func(update, context, *args, **kwargs)
                    # Log successful action
                    self.log_admin_action(
                        admin_id=admin_id,
                        action=action_name,
                        target_user_id=target_user_id,
                        target_group_id=target_group_id,
                        success=True
                    )
                    return result
                except Exception as e:
                    # Log failed action
                    self.log_admin_action(
                        admin_id=admin_id,
                        action=action_name,
                        target_user_id=target_user_id,
                        target_group_id=target_group_id,
                        details={"error": str(e)},
                        success=False
                    )
                    raise

            return wrapper
        return decorator

    @staticmethod
    def create_admin_action_decorator(logging_service, action_name: str):
        """Create a decorator for logging admin actions"""
        def decorator(func):
            @wraps(func)
            async def wrapper(update, context, *args, **kwargs):
                # Extract admin info
                user = update.effective_user
                if not user:
                    return await func(update, context, *args, **kwargs)

                admin_id = user.id

                # Extract target info from context args if available
                target_user_id = None
                target_group_id = None

                if context.args and hasattr(context.args, '__getitem__'):
                    # Try to parse first arg as user ID
                    try:
                        target_user_id = int(context.args[0])
                    except (ValueError, IndexError, TypeError):
                        pass

                # Extract group ID from chat if it's a group
                chat = update.effective_chat
                if chat and chat.type in ['group', 'supergroup']:
                    target_group_id = chat.id

                # Call the function
                try:
                    result = await func(update, context, *args, **kwargs)
                    # Log successful action
                    logging_service.log_admin_action(
                        admin_id=admin_id,
                        action=action_name,
                        target_user_id=target_user_id,
                        target_group_id=target_group_id,
                        success=True
                    )
                    return result
                except Exception as e:
                    # Log failed action
                    logging_service.log_admin_action(
                        admin_id=admin_id,
                        action=action_name,
                        target_user_id=target_user_id,
                        target_group_id=target_group_id,
                        details={"error": str(e)},
                        success=False
                    )
                    raise

            return wrapper
        return decorator