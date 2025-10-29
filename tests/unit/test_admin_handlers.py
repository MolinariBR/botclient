from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Chat, Message, Update
from telegram import User as TelegramUser

from src.handlers.admin_handlers import AdminHandlers
from src.models.admin import Admin
from src.models.group import Group, GroupMembership
from src.models.payment import Payment
from src.models.user import User
from src.models.system_config import SystemConfig
from src.models.scheduled_message import ScheduledMessage


class TestAdminHandlers:
    """Unit tests for Admin handlers"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def mock_telegram_service(self):
        """Mock telegram service"""
        return Mock()

    @pytest.fixture
    def mock_logging_service(self):
        """Mock logging service"""
        return Mock()

    @pytest.fixture
    def admin_handlers(self, mock_db, mock_telegram_service, mock_logging_service):
        """Admin handlers instance"""
        return AdminHandlers(mock_db, mock_telegram_service, mock_logging_service)

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user"""
        user = Mock(spec=TelegramUser)
        user.id = 12345
        return user

    @pytest.fixture
    def mock_regular_user(self):
        """Mock regular user"""
        user = Mock(spec=TelegramUser)
        user.id = 67890
        return user

    @pytest.fixture
    def mock_message(self):
        """Mock message"""
        return Mock(spec=Message)

    @pytest.fixture
    def mock_chat(self):
        """Mock chat"""
        chat = Mock(spec=Chat)
        chat.id = -1001234567890
        chat.title = "Test VIP Group"
        chat.type = "private"  # Default to private for admin commands
        return chat

    def test_kick_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test kick handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.kick_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_kick_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test kick handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.kick_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /kick @username")

    def test_kick_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test kick handler when target user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["nonexistentuser"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [Mock(spec=Admin), None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.kick_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistentuser não encontrado.")

    def test_kick_handler_group_not_registered(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test kick handler when group is not registered"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.telegram_id = "67890"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user,      # User lookup
            None               # Group lookup - not found
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.kick_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Este grupo não está registrado como grupo VIP.")

    def test_kick_handler_user_not_member(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test kick handler when user is not a member of the group"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.telegram_id = "67890"

        mock_group = Mock(spec=Group)
        mock_group.telegram_group_id = str(mock_chat.id)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user,      # User lookup
            mock_group,        # Group lookup
            None               # Membership lookup - not found
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.kick_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @testuser não é membro deste grupo.")

    def test_kick_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test successful kick handler execution"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.telegram_id = "67890"

        mock_group = Mock(spec=Group)
        mock_group.telegram_group_id = str(mock_chat.id)

        mock_membership = Mock(spec=GroupMembership)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user,      # User lookup
            mock_group,        # Group lookup
            mock_membership    # Membership lookup
        ]

        admin_handlers.telegram.kick_chat_member = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.kick_handler(update, context))

        # Assert
        admin_handlers.db.delete.assert_called_once_with(mock_membership)
        admin_handlers.db.commit.assert_called_once()
        admin_handlers.telegram.kick_chat_member.assert_called_once_with(
            int(mock_chat.id), int(mock_db_user.telegram_id)
        )
        mock_message.reply_text.assert_called_once_with("Usuário @testuser removido do grupo com sucesso.")

    def test_kick_handler_telegram_kick_failed(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test kick handler when Telegram kick fails"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.telegram_id = "67890"

        mock_group = Mock(spec=Group)
        mock_group.telegram_group_id = str(mock_chat.id)

        mock_membership = Mock(spec=GroupMembership)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user,      # User lookup
            mock_group,        # Group lookup
            mock_membership    # Membership lookup
        ]

        admin_handlers.telegram.kick_chat_member = AsyncMock(return_value=False)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.kick_handler(update, context))

        # Assert
        admin_handlers.db.delete.assert_called_once_with(mock_membership)
        admin_handlers.db.commit.assert_called_once()
        admin_handlers.telegram.kick_chat_member.assert_called_once_with(
            int(mock_chat.id), int(mock_db_user.telegram_id)
        )
        mock_message.reply_text.assert_called_once_with(
            "Usuário @testuser removido do banco de dados, mas falha ao remover do grupo Telegram."
        )

    # ===== ADD HANDLER TESTS =====

    def test_add_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test add handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_add_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test add handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /add @username <group_telegram_id>")

    def test_add_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test add handler when target user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["nonexistentuser", "123456789"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [Mock(spec=Admin), None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistentuser não encontrado. Certifique-se de que o usuário iniciou uma conversa com o bot.")

    def test_add_handler_group_creation_and_successful_add(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test add handler creates group and successfully adds user"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "123456789"]

        mock_db_user = Mock(spec=User)
        mock_db_user.id = 1
        mock_db_user.username = "testuser"
        mock_db_user.telegram_id = "67890"

        # Mock the query chain
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user,      # User lookup
            None,              # Group lookup - not found
            None               # Membership lookup - not found
        ]

        # Mock db.add and db.commit to simulate group creation
        added_objects = []
        def mock_add(obj):
            added_objects.append(obj)
            if hasattr(obj, 'id'):
                obj.id = len(added_objects)  # Simulate auto-incrementing ID
        admin_handlers.db.add.side_effect = mock_add

        def mock_commit():
            # After commit, the group should have an ID
            for obj in added_objects:
                if hasattr(obj, 'telegram_group_id') and obj.id is None:
                    obj.id = 1  # Set group ID
        admin_handlers.db.commit.side_effect = mock_commit

        admin_handlers.telegram.create_chat_invite_link = AsyncMock(return_value="https://t.me/joinchat/abc123")
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Assert
        # Check that group was created
        group_creation_calls = [call for call in admin_handlers.db.add.call_args_list
                               if hasattr(call[0][0], 'telegram_group_id')]
        assert len(group_creation_calls) == 1
        group = group_creation_calls[0][0][0]
        assert group.telegram_group_id == str(mock_chat.id)
        assert group.name == mock_chat.title

        # Check that membership was added
        membership_calls = [call for call in admin_handlers.db.add.call_args_list
                           if hasattr(call[0][0], 'user_id')]
        assert len(membership_calls) == 1
        membership = membership_calls[0][0][0]
        assert membership.user_id == mock_db_user.id
        assert membership.group_id is not None

        # Check commits
        assert admin_handlers.db.commit.call_count == 2

        # Check Telegram interactions
        admin_handlers.telegram.create_chat_invite_link.assert_called_once_with(
            int(mock_chat.id), name="Convite para testuser"
        )
        admin_handlers.telegram.send_message.assert_called_once_with(
            int(mock_db_user.telegram_id),
            f"Você foi adicionado ao grupo VIP: {mock_chat.title}\n\nLink de convite: https://t.me/joinchat/abc123"
        )

        # Check admin notification
        mock_message.reply_text.assert_called_once_with("Usuário @testuser adicionado com sucesso ao grupo.")

    def test_add_handler_existing_group_successful_add(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test add handler with existing group and successful user addition"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "123456789"]

        mock_db_user = Mock(spec=User)
        mock_db_user.id = 1
        mock_db_user.username = "testuser"
        mock_db_user.telegram_id = "67890"

        mock_group = Mock(spec=Group)
        mock_group.id = 1
        mock_group.telegram_group_id = str(mock_chat.id)
        mock_group.name = mock_chat.title

        # Mock the query chain
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user,      # User lookup
            mock_group,        # Group lookup - found
            None               # Membership lookup - not found
        ]

        admin_handlers.telegram.create_chat_invite_link = AsyncMock(return_value="https://t.me/joinchat/abc123")
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Assert
        # Check that no new group was created
        group_creation_calls = [call for call in admin_handlers.db.add.call_args_list
                               if hasattr(call[0][0], 'telegram_group_id')]
        assert len(group_creation_calls) == 0

        # Check that membership was added
        membership_calls = [call for call in admin_handlers.db.add.call_args_list
                           if hasattr(call[0][0], 'user_id')]
        assert len(membership_calls) == 1
        membership = membership_calls[0][0][0]
        assert membership.user_id == mock_db_user.id
        assert membership.group_id == mock_group.id

        # Check commits
        assert admin_handlers.db.commit.call_count == 1

        # Check admin notification
        mock_message.reply_text.assert_called_once_with("Usuário @testuser adicionado com sucesso ao grupo.")

    def test_add_handler_user_already_member(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test add handler when user is already a member"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "123456789"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"

        mock_membership = Mock(spec=GroupMembership)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),     # Admin check
            mock_db_user,         # User lookup
            Mock(spec=Group),     # Group lookup
            mock_membership       # Membership lookup - already exists
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @testuser já é membro deste grupo.")
        # Should not add anything or commit
        admin_handlers.db.add.assert_not_called()
        admin_handlers.db.commit.assert_not_called()

    def test_add_handler_invite_link_creation_fails(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test add handler when invite link creation fails"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "123456789"]

        mock_db_user = Mock(spec=User)
        mock_db_user.id = 1
        mock_db_user.username = "testuser"
        mock_db_user.telegram_id = "67890"

        # Mock the query chain
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user,      # User lookup
            None,              # Group lookup - not found
            None               # Membership lookup - not found
        ]

        admin_handlers.telegram.create_chat_invite_link = AsyncMock(return_value=None)
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Assert
        # Check that membership was still added
        membership_calls = [call for call in admin_handlers.db.add.call_args_list
                           if hasattr(call[0][0], 'user_id')]
        assert len(membership_calls) == 1

        # Check notification sent without invite link
        admin_handlers.telegram.send_message.assert_called_once_with(
            int(mock_db_user.telegram_id),
            f"Você foi adicionado ao grupo VIP: {mock_chat.title}\n\nEntre em contato com o admin para acesso."
        )

        # Check admin notification
        mock_message.reply_text.assert_called_once_with("Usuário @testuser adicionado com sucesso ao grupo.")

    def test_add_handler_notification_fails(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test add handler when user notification fails"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "123456789"]

        mock_db_user = Mock(spec=User)
        mock_db_user.id = 1
        mock_db_user.username = "testuser"
        mock_db_user.telegram_id = "67890"

        # Mock the query chain
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user,      # User lookup
            None,              # Group lookup - not found
            None               # Membership lookup - not found
        ]

        admin_handlers.telegram.create_chat_invite_link = AsyncMock(return_value="https://t.me/joinchat/abc123")
        admin_handlers.telegram.send_message = AsyncMock(return_value=False)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.add_handler(update, context))

        # Assert
        # Check that membership was still added
        membership_calls = [call for call in admin_handlers.db.add.call_args_list
                           if hasattr(call[0][0], 'user_id')]
        assert len(membership_calls) == 1

        # Check admin notification about notification failure
        mock_message.reply_text.assert_called_once_with(
            "Usuário @testuser adicionado ao banco de dados, mas falha ao notificar."
        )

    # ===== BAN HANDLER TESTS =====

    def test_ban_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test ban handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.ban_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_ban_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test ban handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.ban_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /ban @username")

    def test_ban_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test ban handler when target user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["nonexistentuser"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [Mock(spec=Admin), None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.ban_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistentuser não encontrado.")

    def test_ban_handler_user_already_banned(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test ban handler when user is already banned"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.is_banned = True

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.ban_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @testuser já está banido.")
        # Should not modify user or commit
        assert not hasattr(mock_db_user, '_is_banned_modified')
        admin_handlers.db.commit.assert_not_called()

    def test_ban_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test successful ban handler execution"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.is_banned = False

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Mock the memberships query to return empty list
        admin_handlers.db.query.return_value.filter_by.return_value.all.return_value = []

        # Execute
        import asyncio
        asyncio.run(admin_handlers.ban_handler(update, context))

        # Assert
        # Check that user was banned
        assert mock_db_user.is_banned == True
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Usuário @testuser banido permanentemente.")

    def test_ban_handler_remove_from_all_groups(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test ban handler removes user from all groups"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_db_user = Mock(spec=User)
        mock_db_user.id = 1
        mock_db_user.username = "testuser"
        mock_db_user.is_banned = False

        mock_membership1 = Mock(spec=GroupMembership)
        mock_membership2 = Mock(spec=GroupMembership)

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Mock the memberships query to return memberships
        admin_handlers.db.query.return_value.filter_by.return_value.all.return_value = [
            mock_membership1, mock_membership2
        ]

        admin_handlers.telegram.kick_chat_member = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.ban_handler(update, context))

        # Assert
        # Check that user was banned
        assert mock_db_user.is_banned == True

        # Check that all memberships were deleted
        admin_handlers.db.delete.assert_any_call(mock_membership1)
        admin_handlers.db.delete.assert_any_call(mock_membership2)
        assert admin_handlers.db.delete.call_count == 2

        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Usuário @testuser banido permanentemente.")

    # ===== MUTE HANDLER TESTS =====

    def test_mute_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test mute handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "10"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.mute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_mute_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test mute handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.mute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /mute @username <minutos>")

    def test_mute_handler_insufficient_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test mute handler with insufficient arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.mute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /mute @username <minutos>")

    def test_mute_handler_invalid_duration(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test mute handler with invalid duration"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "invalid"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.mute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Duração inválida. Use um número de minutos.")

    def test_mute_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test mute handler when target user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["nonexistentuser", "10"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [Mock(spec=Admin), None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.mute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistentuser não encontrado.")

    def test_mute_handler_user_already_muted(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test mute handler when user is already muted"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "10"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.is_muted = True

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.mute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @testuser já está silenciado.")
        # Should not modify user or commit
        assert not hasattr(mock_db_user, '_is_muted_modified')
        admin_handlers.db.commit.assert_not_called()

    def test_mute_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test successful mute handler execution"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "10"]

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.is_muted = False

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.mute_handler(update, context))

        # Assert
        # Check that user was muted
        assert mock_db_user.is_muted == True
        # Check that mute_until was set (we can't check exact time due to mocking)
        assert hasattr(mock_db_user, 'mute_until')
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Usuário @testuser silenciado por 10 minutos.")

    def test_mute_handler_zero_duration_unmutes(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test mute handler with zero duration unmutes user"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser", "0"]

        mock_db_user = Mock()
        mock_db_user.username = "testuser"
        mock_db_user.is_muted = True

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.mute_handler(update, context))

        # Assert
        # Check that user was unmuted
        assert mock_db_user.is_muted == False
        assert mock_db_user.mute_until == None
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Usuário @testuser teve o silêncio removido.")

    # ===== BROADCAST HANDLER TESTS =====

    def test_broadcast_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test broadcast handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["Test", "message"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.broadcast_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_broadcast_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test broadcast handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.broadcast_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /broadcast <mensagem>")

    def test_broadcast_handler_empty_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test broadcast handler with empty arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = []

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.broadcast_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /broadcast <mensagem>")

    def test_broadcast_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test successful broadcast handler execution"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["Hello", "world", "test"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Mock the broadcast logic (will be tested in integration tests)
        admin_handlers._broadcast_to_all_members = AsyncMock()

        # Execute
        import asyncio
        asyncio.run(admin_handlers.broadcast_handler(update, context))

        # Assert
        admin_handlers._broadcast_to_all_members.assert_called_once_with("Hello world test")
        mock_message.reply_text.assert_called_once_with("Mensagem enviada para todos os membros!")

    def test_unban_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test unban handler rejects non-admin users"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_chat.type = "private"

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unban_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")
        admin_handlers.db.commit.assert_not_called()

    def test_unban_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test unban handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = []

        mock_chat.type = "private"

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unban_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /unban @username")
        admin_handlers.db.commit.assert_not_called()

    def test_unban_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test unban handler when user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["nonexistent"]

        mock_chat.type = "private"

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            None               # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unban_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistent não encontrado.")
        admin_handlers.db.commit.assert_not_called()

    def test_unban_handler_user_already_unbanned(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test unban handler when user is already unbanned"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_chat.type = "private"

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.is_banned = False

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unban_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @testuser não está banido.")
        admin_handlers.db.commit.assert_not_called()

    def test_unban_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test successful unban handler execution"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_chat.type = "private"

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.is_banned = True

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unban_handler(update, context))

        # Assert
        # Check that commit was called (user was unbanned)
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Usuário @testuser desbanido com sucesso.")

    def test_unmute_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test unmute handler rejects non-admin users"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_chat.type = "private"

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unmute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")
        admin_handlers.db.commit.assert_not_called()

    def test_unmute_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test unmute handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = []

        mock_chat.type = "private"

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unmute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /unmute @username")
        admin_handlers.db.commit.assert_not_called()

    def test_unmute_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test unmute handler when user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["nonexistent"]

        mock_chat.type = "private"

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            None               # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unmute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistent não encontrado.")
        admin_handlers.db.commit.assert_not_called()

    def test_unmute_handler_user_already_unmuted(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test unmute handler when user is already unmuted"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_chat.type = "private"

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.is_muted = False

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unmute_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @testuser não está mutado.")
        admin_handlers.db.commit.assert_not_called()

    def test_unmute_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test successful unmute handler execution"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_chat.type = "private"

        mock_db_user = Mock(spec=User)
        mock_db_user.username = "testuser"
        mock_db_user.is_muted = True

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.unmute_handler(update, context))

        # Assert
        # Check that commit was called (user was unmuted)
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Usuário @testuser desmutado com sucesso.")

    def test_userinfo_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test userinfo handler rejects non-admin users"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_chat.type = "private"

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.userinfo_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")
        admin_handlers.db.commit.assert_not_called()

    def test_userinfo_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test userinfo handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = []

        mock_chat.type = "private"

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.userinfo_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /userinfo @username")
        admin_handlers.db.commit.assert_not_called()

    def test_userinfo_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test userinfo handler when user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["nonexistent"]

        mock_chat.type = "private"

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            None               # User lookup
        ]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.userinfo_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistent não encontrado.")
        admin_handlers.db.commit.assert_not_called()

    def test_userinfo_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test successful userinfo handler execution"""
        from datetime import datetime

        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["testuser"]

        mock_chat.type = "private"

        mock_db_user = Mock(spec=User)
        mock_db_user.id = 1
        mock_db_user.telegram_id = "123456789"
        mock_db_user.username = "testuser"
        mock_db_user.status_assinatura = "active"
        mock_db_user.data_expiracao = datetime(2025, 12, 31)
        mock_db_user.is_banned = False
        mock_db_user.is_muted = False
        mock_db_user.mute_until = None
        mock_db_user.warn_count = 1
        mock_db_user.auto_renew = True
        mock_db_user.created_at = datetime(2025, 1, 1)

        # Mock payments
        mock_payment1 = Mock()
        mock_payment1.status = "completed"
        mock_payment1.amount = 10.0
        mock_payment2 = Mock()
        mock_payment2.status = "pending"
        mock_payment2.amount = 5.0

        # Mock the query chain for admin check and user lookup
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [
            Mock(spec=Admin),  # Admin check
            mock_db_user       # User lookup
        ]
        admin_handlers.db.query.return_value.filter_by.return_value.all.return_value = [mock_payment1, mock_payment2]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.userinfo_handler(update, context))

        # Assert
        # Check that message was sent with user info
        args, kwargs = mock_message.reply_text.call_args
        message_text = args[0]
        assert "👤 **Informações do Usuário: @testuser**" in message_text
        assert "🆔 **ID Telegram:** 123456789" in message_text
        assert "💳 **Status VIP:** Ativo" in message_text
        assert "🚫 **Banido:** Não" in message_text
        assert "🔇 **Mutado:** Não" in message_text
        assert "⚠️ **Avisos:** 1/3" in message_text
        assert "🔄 **Renovação automática:** Sim" in message_text
        assert "💰 **Pagamentos:**" in message_text
        assert "Total: 2" in message_text
        assert "Concluídos: 1" in message_text
        assert "Pendentes: 1" in message_text
        assert kwargs.get("parse_mode") == "Markdown"

    def test_pending_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test pending handler rejects non-admin users"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = []

        mock_chat.type = "private"

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.pending_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")
        admin_handlers.db.commit.assert_not_called()

    def test_pending_handler_no_pending_payments(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test pending handler when there are no pending payments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = []

        mock_chat.type = "private"

        # Mock the query chain for admin check
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)
        # Mock empty pending payments
        admin_handlers.db.query.return_value.filter_by.return_value.all.return_value = []

        # Execute
        import asyncio
        asyncio.run(admin_handlers.pending_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("✅ Não há pagamentos pendentes.")

    def test_pending_handler_with_pending_payments(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test pending handler with pending payments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = []

        mock_chat.type = "private"

        # Mock users
        mock_user1 = Mock(spec=User)
        mock_user1.id = 1
        mock_user1.username = "user1"
        mock_user1.telegram_id = "111111111"

        mock_user2 = Mock(spec=User)
        mock_user2.id = 2
        mock_user2.username = "user2"
        mock_user2.telegram_id = "222222222"

        # Mock payments
        mock_payment1 = Mock()
        mock_payment1.user_id = 1
        mock_payment1.amount = 10.0

        mock_payment2 = Mock()
        mock_payment2.user_id = 1
        mock_payment2.amount = 5.0

        mock_payment3 = Mock()
        mock_payment3.user_id = 2
        mock_payment3.amount = 15.0

        # Create separate mock query objects
        mock_payment_query = Mock()
        mock_payment_query.filter_by.return_value.all.return_value = [mock_payment1, mock_payment2, mock_payment3]

        mock_user_query = Mock()
        mock_user_query.filter_by.return_value.first.side_effect = [mock_user1, mock_user2]

        # Mock the db.query to return different query objects based on the model
        def mock_query(model):
            if model == Payment:
                return mock_payment_query
            elif model == Admin:
                mock_admin_query = Mock()
                mock_admin_query.filter_by.return_value.first.return_value = Mock(spec=Admin)
                return mock_admin_query
            elif model == User:
                return mock_user_query
            return Mock()

        admin_handlers.db.query.side_effect = mock_query

        # Execute
        import asyncio
        asyncio.run(admin_handlers.pending_handler(update, context))

        # Assert
        args, kwargs = mock_message.reply_text.call_args
        message_text = args[0]
        assert "📋 **Pagamentos Pendentes:**" in message_text
        assert "@user1" in message_text
        assert "R$ 15.00" in message_text  # 10 + 5
        assert "@user2" in message_text
        assert "R$ 15.00" in message_text
        assert kwargs.get("parse_mode") == "Markdown"

    def test_warn_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test warn handler when user is not admin"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_regular_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser", "spamming"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.warn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_warn_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test warn handler when not in private chat"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["@testuser", "spamming"]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.warn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_warn_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test warn handler with no arguments"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.warn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /warn @username <motivo>")

    def test_warn_handler_insufficient_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test warn handler with insufficient arguments"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.warn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /warn @username <motivo>")

    def test_warn_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test warn handler when user is not found"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@nonexistent", "spamming"]

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.warn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistent não encontrado. Certifique-se de que o usuário iniciou uma conversa com o bot.")

    def test_warn_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test warn handler successful warning"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser", "spamming", "in", "chat"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.warn_count = 0
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.warn_handler(update, context))

        # Assert
        assert mock_user.warn_count == 1
        admin_handlers.db.add.assert_called_once()
        admin_handlers.db.commit.assert_called_once()
        admin_handlers.telegram.send_message.assert_called_once_with(
            123456789,
            "⚠️ Você recebeu um aviso do administrador.\n\nMotivo: spamming in chat\nAvisos totais: 1"
        )
        mock_message.reply_text.assert_called_once_with("Usuário @testuser avisado com sucesso. Motivo: spamming in chat")

    def test_warn_handler_notification_fails(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test warn handler when notification fails"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser", "spamming"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.warn_count = 0
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]
        admin_handlers.telegram.send_message = AsyncMock(return_value=False)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.warn_handler(update, context))

        # Assert
        assert mock_user.warn_count == 1
        admin_handlers.db.add.assert_called_once()
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Aviso registrado para @testuser, mas falha ao notificar o usuário.")

    def test_resetwarn_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test resetwarn handler when user is not admin"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_regular_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.resetwarn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_resetwarn_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test resetwarn handler when not in private chat"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["@testuser"]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.resetwarn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_resetwarn_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test resetwarn handler with no arguments"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.resetwarn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /resetwarn @username")

    def test_resetwarn_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test resetwarn handler when user is not found"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@nonexistent"]

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.resetwarn_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistent não encontrado. Certifique-se de que o usuário iniciou uma conversa com o bot.")

    def test_resetwarn_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test resetwarn handler successful reset"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.warn_count = 3
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]
        admin_handlers.db.query.return_value.filter_by.return_value.delete.return_value = 3
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.resetwarn_handler(update, context))

        # Assert
        assert mock_user.warn_count == 0
        admin_handlers.db.commit.assert_called_once()
        admin_handlers.telegram.send_message.assert_called_once_with(
            123456789,
            "✅ Seus avisos foram resetados pelo administrador.\nAvisos anteriores: 3"
        )
        mock_message.reply_text.assert_called_once_with("Avisos de @testuser resetados com sucesso. 3 avisos removidos.")

    def test_resetwarn_handler_notification_fails(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test resetwarn handler when notification fails"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.warn_count = 2
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]
        admin_handlers.db.query.return_value.filter_by.return_value.delete.return_value = 2
        admin_handlers.telegram.send_message = AsyncMock(return_value=False)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.resetwarn_handler(update, context))

        # Assert
        assert mock_user.warn_count == 0
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Avisos de @testuser resetados, mas falha ao notificar o usuário.")

    def test_expire_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test expire handler when user is not admin"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_regular_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.expire_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_expire_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test expire handler when not in private chat"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["@testuser"]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.expire_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_expire_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test expire handler with no arguments"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.expire_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /expire @username")

    def test_expire_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test expire handler when user is not found"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@nonexistent"]

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.expire_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistent não encontrado. Certifique-se de que o usuário iniciou uma conversa com o bot.")

    def test_expire_handler_no_active_subscription(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test expire handler when user has no active subscription"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.status_assinatura = "expired"
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.expire_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @testuser não possui uma assinatura ativa.")

    def test_expire_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test expire handler successful expiration"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.status_assinatura = "active"
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.expire_handler(update, context))

        # Assert
        assert mock_user.status_assinatura == "expired"
        admin_handlers.db.commit.assert_called_once()
        admin_handlers.telegram.send_message.assert_called_once_with(
            123456789,
            "❌ Sua assinatura VIP foi expirada pelo administrador."
        )
        mock_message.reply_text.assert_called_once_with("Assinatura de @testuser expirada com sucesso.")

    def test_expire_handler_notification_fails(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test expire handler when notification fails"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.status_assinatura = "active"
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]
        admin_handlers.telegram.send_message = AsyncMock(return_value=False)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.expire_handler(update, context))

        # Assert
        assert mock_user.status_assinatura == "expired"
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("Assinatura de @testuser expirada, mas falha ao notificar o usuário.")

    def test_sendto_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test sendto handler when user is not admin"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_regular_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser", "hello"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.sendto_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_sendto_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test sendto handler when not in private chat"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["@testuser", "hello"]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.sendto_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_sendto_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test sendto handler with no arguments"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.sendto_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /sendto @username <mensagem>")

    def test_sendto_handler_insufficient_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test sendto handler with insufficient arguments"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser"]

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.sendto_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /sendto @username <mensagem>")

    def test_sendto_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test sendto handler when user is not found"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@nonexistent", "hello", "world"]

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.sendto_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário @nonexistent não encontrado. Certifique-se de que o usuário iniciou uma conversa com o bot.")

    def test_sendto_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test sendto handler successful message send"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser", "hello", "world", "message"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]
        admin_handlers.telegram.send_message = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.sendto_handler(update, context))

        # Assert
        admin_handlers.telegram.send_message.assert_called_once_with(
            123456789,
            "📩 Mensagem do administrador:\n\nhello world message"
        )
        mock_message.reply_text.assert_called_once_with("Mensagem enviada com sucesso para @testuser.")

    def test_sendto_handler_send_fails(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test sendto handler when message send fails"""
        # Setup
        update = Update(update_id=1, message=mock_message)
        mock_message.from_user = mock_admin_user
        mock_message.chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["@testuser", "hello", "world"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_user = Mock(spec=User)
        mock_user.id = 2
        mock_user.telegram_id = "123456789"
        mock_user.username = "testuser"

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_user]
        admin_handlers.telegram.send_message = AsyncMock(return_value=False)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.sendto_handler(update, context))

        # Assert
        admin_handlers.telegram.send_message.assert_called_once_with(
            123456789,
            "📩 Mensagem do administrador:\n\nhello world"
        )
        mock_message.reply_text.assert_called_once_with("Falha ao enviar mensagem para @testuser.")

    def test_setprice_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test setprice handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["50", "BRL"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setprice_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_setprice_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setprice handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["50", "BRL"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setprice_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_setprice_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setprice handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setprice_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /setprice <preço> <moeda>\nExemplo: /setprice 50 BRL")

    def test_setprice_handler_invalid_price(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setprice handler with invalid price"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["invalid", "BRL"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setprice_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Preço deve ser um número válido.")

    def test_setprice_handler_negative_price(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setprice handler with negative price"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["-50", "BRL"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setprice_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Preço deve ser um valor positivo.")

    def test_setprice_handler_invalid_currency(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setprice handler with invalid currency"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["50", "INVALID"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setprice_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Moeda inválida. Use uma das seguintes: BRL, USD, EUR")

    def test_setprice_handler_success_new_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setprice handler success creating new config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["50.00", "BRL"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setprice_handler(update, context))

        # Assert
        admin_handlers.db.add.assert_called_once()
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Preço da assinatura atualizado com sucesso!\n\nNovo preço: 50.00 BRL")

    def test_setprice_handler_success_update_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setprice handler success updating existing config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["75.50", "USD"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_config = Mock(spec=SystemConfig)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_config]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setprice_handler(update, context))

        # Assert
        assert mock_config.value == "75.50 USD"
        assert mock_config.updated_by == 1
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Preço da assinatura atualizado com sucesso!\n\nNovo preço: 75.50 USD")

    def test_settime_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test settime handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["30"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.settime_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_settime_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test settime handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["30"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.settime_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_settime_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test settime handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.settime_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /settime <dias>\nExemplo: /settime 30")

    def test_settime_handler_invalid_days(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test settime handler with invalid days"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["invalid"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.settime_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Número de dias deve ser um número inteiro válido.")

    def test_settime_handler_negative_days(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test settime handler with negative days"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["-30"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.settime_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Número de dias deve ser positivo.")

    def test_settime_handler_success_new_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test settime handler success creating new config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["45"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.settime_handler(update, context))

        # Assert
        admin_handlers.db.add.assert_called_once()
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Duração da assinatura atualizada com sucesso!\n\nNova duração: 45 dias")

    def test_settime_handler_success_update_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test settime handler success updating existing config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["60"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_config = Mock(spec=SystemConfig)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_config]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.settime_handler(update, context))

        # Assert
        assert mock_config.value == "60"
        assert mock_config.updated_by == 1
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Duração da assinatura atualizada com sucesso!\n\nNova duração: 60 dias")

    def test_setwallet_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test setwallet handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["0x1234567890abcdef"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setwallet_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_setwallet_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setwallet handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["0x1234567890abcdef"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setwallet_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_setwallet_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setwallet handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setwallet_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /setwallet <endereço_da_carteira>\nExemplo: /setwallet 0x1234567890abcdef")

    def test_setwallet_handler_invalid_wallet(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setwallet handler with invalid wallet address"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["invalid"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setwallet_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Endereço de carteira inválido. Deve começar com '0x' e ter pelo menos 10 caracteres.")

    def test_setwallet_handler_success_new_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setwallet handler success creating new config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["0x1234567890abcdef1234567890abcdef"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setwallet_handler(update, context))

        # Assert
        admin_handlers.db.add.assert_called_once()
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Carteira USDT atualizada com sucesso!\n\nNova carteira: `0x1234567890abcdef1234567890abcdef`")

    def test_setwallet_handler_success_update_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test setwallet handler success updating existing config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["0xabcdef1234567890abcdef1234567890"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_config = Mock(spec=SystemConfig)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_config]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.setwallet_handler(update, context))

        # Assert
        assert mock_config.value == "0xabcdef1234567890abcdef1234567890"
        assert mock_config.updated_by == 1
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Carteira USDT atualizada com sucesso!\n\nNova carteira: `0xabcdef1234567890abcdef1234567890`")

    def test_rules_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test rules handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["Respeite", "todos"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.rules_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_rules_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test rules handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["Respeite", "todos"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.rules_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_rules_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test rules handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.rules_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /rules <texto das regras>\nExemplo: /rules Bem-vindo! Respeite todos os membros.")

    def test_rules_handler_success_new_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test rules handler success creating new config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["Respeite", "todos", "os", "membros"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.rules_handler(update, context))

        # Assert
        admin_handlers.db.add.assert_called_once()
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Regras do grupo atualizadas com sucesso!\n\nRegras: Respeite todos os membros")

    def test_rules_handler_success_update_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test rules handler success updating existing config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["Seja", "respeitoso"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_config = Mock(spec=SystemConfig)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_config]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.rules_handler(update, context))

        # Assert
        assert mock_config.value == "Seja respeitoso"
        assert mock_config.updated_by == 1
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Regras do grupo atualizadas com sucesso!\n\nRegras: Seja respeitoso")

    def test_welcome_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test welcome handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["Bem-vindo"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.welcome_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_welcome_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test welcome handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["Bem-vindo"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.welcome_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_welcome_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test welcome handler with no arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = None

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.welcome_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /welcome <texto de boas-vindas>\nExemplo: /welcome Bem-vindo ao nosso grupo VIP!")

    def test_welcome_handler_success_new_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test welcome handler success creating new config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["Bem-vindo", "ao", "nosso", "grupo"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.welcome_handler(update, context))

        # Assert
        admin_handlers.db.add.assert_called_once()
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Mensagem de boas-vindas atualizada com sucesso!\n\nMensagem: Bem-vindo ao nosso grupo")

    def test_welcome_handler_success_update_config(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test welcome handler success updating existing config"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["Olá", "e", "bem-vindo"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_config = Mock(spec=SystemConfig)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_config]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.welcome_handler(update, context))

        # Assert
        assert mock_config.value == "Olá e bem-vindo"
        assert mock_config.updated_by == 1
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Mensagem de boas-vindas atualizada com sucesso!\n\nMensagem: Olá e bem-vindo")

    def test_schedule_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test schedule handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()
        context.args = ["09:00", "Bom", "dia"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.schedule_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_schedule_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test schedule handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()
        context.args = ["09:00", "Bom", "dia"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.schedule_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_schedule_handler_no_args(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test schedule handler with insufficient arguments"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["09:00"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.schedule_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Uso: /schedule <HH:MM> <mensagem>\nExemplo: /schedule 09:00 Bom dia a todos!")

    def test_schedule_handler_invalid_time(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test schedule handler with invalid time format"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["25:00", "Mensagem"]

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = Mock(spec=Admin)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.schedule_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Formato de horário inválido. Use HH:MM (exemplo: 09:00)")

    def test_schedule_handler_schedule_exists(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test schedule handler when schedule already exists for the time"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["09:00", "Bom", "dia"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        mock_existing_schedule = Mock(spec=ScheduledMessage)

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, mock_existing_schedule]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.schedule_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Já existe uma mensagem agendada para 09:00. Use outro horário.")

    def test_schedule_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test schedule handler success"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()
        context.args = ["09:00", "Bom", "dia", "a", "todos"]

        mock_admin = Mock(spec=Admin)
        mock_admin.id = 1

        admin_handlers.db.query.return_value.filter_by.return_value.first.side_effect = [mock_admin, None]

        # Execute
        import asyncio
        asyncio.run(admin_handlers.schedule_handler(update, context))

        # Assert
        admin_handlers.db.add.assert_called_once()
        admin_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Mensagem agendada com sucesso!\n\nHorário: 09:00\nMensagem: Bom dia a todos")

    def test_stats_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test stats handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.stats_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_stats_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test stats handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.stats_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_stats_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test stats handler success case"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Mock all database queries to return the expected values
        # This is a simplified approach - just mock the final results
        admin_handlers.db.query.return_value.count.side_effect = [100, 5, 10, 50, 75, 25, 3]

        # Mock the sum query
        mock_sum_query = Mock()
        mock_sum_query.scalar.return_value = 2500.50
        admin_handlers.db.query.return_value.query.return_value = mock_sum_query

        # Execute
        import asyncio
        asyncio.run(admin_handlers.stats_handler(update, context))

        # Assert
        expected_text = """📊 **Estatísticas do Sistema**

👥 **Usuários:**
• Total: 100
• Com assinatura ativa: 75

👨‍💼 **Administradores:** 5

👥 **Grupos:** 10

💰 **Pagamentos:**
• Total de transações: 50
• Valor total: R$ 2500.50
• Pagamentos recentes (30 dias): 25

📅 **Mensagens Agendadas:** 3

📈 **Resumo:** Sistema saudável com 75 usuários ativos"""
        mock_message.reply_text.assert_called_once_with(expected_text)

    def test_stats_handler_database_error(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test stats handler when database error occurs"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Mock database to raise exception
        admin_handlers.db.query.side_effect = Exception("Database error")

        # Execute
        import asyncio
        asyncio.run(admin_handlers.stats_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Falha ao obter estatísticas do sistema.")

    def test_backup_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test backup handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.backup_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_backup_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test backup handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.backup_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_backup_handler_success(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test backup handler success case"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Mock models - return empty lists for all tables
        admin_handlers.db.query.return_value.all.side_effect = [
            [],  # users
            [],  # admins
            [],  # groups
            [],  # payments
            [],  # warnings
            [],  # memberships
            [],  # configs
            []   # scheduled messages
        ]

        # Mock telegram service
        admin_handlers.telegram.send_document = AsyncMock(return_value=True)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.backup_handler(update, context))

        # Assert
        admin_handlers.telegram.send_document.assert_called_once()
        mock_message.reply_text.assert_called_once_with("✅ Backup criado e enviado com sucesso!")

    def test_restore_handler_not_admin(self, admin_handlers, mock_regular_user, mock_message, mock_chat):
        """Test restore handler when user is not admin"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_regular_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.restore_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Acesso negado. Você não é um administrador.")

    def test_restore_handler_not_private_chat(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test restore handler when not in private chat"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "group"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        # Execute
        import asyncio
        asyncio.run(admin_handlers.restore_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")

    def test_restore_handler_no_document(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test restore handler when no document is attached"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        mock_message.document = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.restore_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Envie um arquivo de backup junto com o comando /restore")

    def test_restore_handler_invalid_file_extension(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test restore handler with invalid file extension"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        mock_document = Mock()
        mock_document.file_name = "backup.txt"
        mock_message.document = mock_document

        # Execute
        import asyncio
        asyncio.run(admin_handlers.restore_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("Arquivo de backup deve ter extensão .json")

    @patch('json.loads')
    def test_restore_handler_invalid_json(self, mock_json_loads, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test restore handler with invalid JSON"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        mock_document = Mock()
        mock_document.file_name = "backup.json"
        mock_document.get_file = AsyncMock()
        mock_file = Mock()
        mock_file.download_as_bytearray = AsyncMock(return_value=b'invalid json')
        mock_document.get_file.return_value = mock_file
        mock_message.document = mock_document

        import json
        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        # Execute
        import asyncio
        asyncio.run(admin_handlers.restore_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Arquivo de backup inválido - erro ao ler JSON.")

    @patch('json.loads')
    def test_restore_handler_success(self, mock_json_loads, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test restore handler success case"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_admin_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        mock_admin = Mock(spec=Admin)
        admin_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_admin

        mock_document = Mock()
        mock_document.file_name = "backup.json"
        mock_document.get_file = AsyncMock()
        mock_file = Mock()
        mock_file.download_as_bytearray = AsyncMock(return_value=b'{"version": "1.0", "tables": {"users": [], "admins": [], "groups": [], "payments": [], "warnings": [], "group_memberships": [], "system_configs": [], "scheduled_messages": []}}')
        mock_document.get_file.return_value = mock_file
        mock_message.document = mock_document

        backup_data = {
            "version": "1.0",
            "tables": {
                "users": [],
                "admins": [],
                "groups": [],
                "payments": [],
                "warnings": [],
                "group_memberships": [],
                "system_configs": [],
                "scheduled_messages": []
            }
        }
        mock_json_loads.return_value = backup_data

        # Mock delete operations
        admin_handlers.db.query.return_value.delete.return_value = None

        # Execute
        import asyncio
        asyncio.run(admin_handlers.restore_handler(update, context))

        # Assert
        assert mock_message.reply_text.call_count == 2
        
        # Check first call (confirmation message)
        first_call_args = mock_message.reply_text.call_args_list[0][0][0]
        assert "⚠️ **ATENÇÃO:** Esta operação irá substituir todos os dados atuais!" in first_call_args
        
        # Check second call (success message)
        second_call_args = mock_message.reply_text.call_args_list[1][0][0]
        assert "✅ **Restauração concluída com sucesso!**" in second_call_args
