from unittest.mock import AsyncMock, Mock

import pytest
from telegram import Chat, Message, Update
from telegram import User as TelegramUser

from src.handlers.admin_handlers import AdminHandlers
from src.models.admin import Admin
from src.models.group import Group, GroupMembership
from src.models.user import User


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
    def admin_handlers(self, mock_db, mock_telegram_service):
        """Admin handlers instance"""
        return AdminHandlers(mock_db, mock_telegram_service)

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
        mock_message.reply_text.assert_called_once_with("Uso: /add @username")

    def test_add_handler_user_not_found(self, admin_handlers, mock_admin_user, mock_message, mock_chat):
        """Test add handler when target user is not found"""
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
        context.args = ["testuser"]

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
        context.args = ["testuser"]

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
        context.args = ["testuser"]

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
        context.args = ["testuser"]

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
        context.args = ["testuser"]

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
