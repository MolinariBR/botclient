from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Chat, Message, Update
from telegram import User as TelegramUser

from src.handlers.user_handlers import UserHandlers
from src.services.pixgo_service import PixGoService
from src.services.usdt_service import USDTService
from src.utils.config import Config


class TestUserHandlers:
    """Unit tests for User handlers"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def mock_pixgo_service(self):
        """Mock PixGo service"""
        service = Mock(spec=PixGoService)
        service.create_payment = Mock(return_value={
            "id": "pix_123",
            "qr_code": "qr_code_data"
        })
        service.get_qr_code = Mock(return_value="QR_CODE_DATA")
        return service

    @pytest.fixture
    def mock_usdt_service(self):
        """Mock USDT service"""
        service = Mock(spec=USDTService)
        service.get_payment_instructions = Mock(return_value="USDT payment instructions")
        return service

    @pytest.fixture
    def user_handlers(self, mock_db, mock_pixgo_service, mock_usdt_service):
        """User handlers instance"""
        return UserHandlers(mock_db, mock_pixgo_service, mock_usdt_service)

    @pytest.fixture
    def mock_telegram_user(self):
        """Mock Telegram user"""
        user = Mock(spec=TelegramUser)
        user.id = 12345
        user.username = "testuser"
        user.first_name = "Test"
        user.last_name = "User"
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
        return chat

    @pytest.mark.asyncio
    async def test_pay_handler_user_already_active(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /pay handler when user already has active subscription"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock existing active user
        mock_db_user = Mock()
        mock_db_user.status_assinatura = "active"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_db_user

        # Execute
        await user_handlers.pay_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("Você já possui uma assinatura ativa!")
        mock_db.query.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.handlers.user_handlers.Payment")
    async def test_pay_handler_successful_pix_payment(self, mock_payment_class, user_handlers, mock_telegram_user, mock_message, mock_chat, mock_db, mock_pixgo_service):
        """Test /pay handler with successful PIX payment creation"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        # Mock inactive user
        mock_db_user = Mock()
        mock_db_user.status_assinatura = "inactive"
        mock_db_user.id = 1
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [mock_db_user, None]

        mock_message.reply_text = AsyncMock()

        # Execute
        await user_handlers.pay_handler(update, context)

        # Assert
        mock_pixgo_service.create_payment.assert_called_once_with(
            amount=Config.SUBSCRIPTION_PRICE,
            description=f"Assinatura VIP - {mock_telegram_user.username}",
            payer_info={"telegram_id": str(mock_telegram_user.id)}
        )
        mock_pixgo_service.get_qr_code.assert_called_once_with("pix_123")

        # Check that payment was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Check response message
        mock_message.reply_text.assert_called_once()
        call_args = mock_message.reply_text.call_args[0][0]
        assert "🎯 **Pagamento PIX**" in call_args
        assert f"R$ {Config.SUBSCRIPTION_PRICE:.2f}" in call_args
        assert "QR_CODE_DATA" in call_args

    @pytest.mark.asyncio
    async def test_pay_handler_pix_payment_failed_fallback_to_usdt(self, user_handlers, mock_telegram_user, mock_message, mock_db, mock_pixgo_service, mock_usdt_service):
        """Test /pay handler when PIX payment fails and falls back to USDT"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock inactive user
        mock_db_user = Mock()
        mock_db_user.status_assinatura = "inactive"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_db_user

        # Mock PIX payment failure
        mock_pixgo_service.create_payment.return_value = None
        mock_message.reply_text = AsyncMock()

        # Execute
        await user_handlers.pay_handler(update, context)

        # Assert
        mock_pixgo_service.create_payment.assert_called_once()
        mock_usdt_service.get_payment_instructions.assert_called_once_with(Config.SUBSCRIPTION_PRICE)
        mock_message.reply_text.assert_called_once_with(
            "PIX indisponível. Use USDT:\nUSDT payment instructions"
        )

    @pytest.mark.asyncio
    @patch("src.handlers.user_handlers.Payment")
    async def test_pay_handler_new_user_creation(self, mock_payment_class, user_handlers, mock_telegram_user, mock_message, mock_chat, mock_db, mock_pixgo_service):
        """Test /pay handler handles payment creation when user doesn't exist in DB"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        # Mock no existing user
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_message.reply_text = AsyncMock()

        # Execute
        await user_handlers.pay_handler(update, context)

        # Assert
        # Should create payment with user_id=None since user doesn't exist
        mock_payment_class.assert_called_once()
        call_args = mock_payment_class.call_args
        assert call_args[1]["user_id"] is None  # user_id should be None
        assert call_args[1]["amount"] == Config.SUBSCRIPTION_PRICE

    @pytest.mark.asyncio
    async def test_status_handler_existing_user(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /status handler with existing user"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock existing user
        mock_db_user = Mock()
        mock_db_user.status_assinatura = "active"
        mock_db_user.data_expiracao = "2025-12-31"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_db_user

        mock_message.reply_text = AsyncMock()

        # Execute
        await user_handlers.status_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once()
        response = mock_message.reply_text.call_args[0][0]
        assert "📊 **Status da Assinatura**" in response
        assert "Active" in response  # Status gets title-cased
        assert "2025-12-31" in response

    @pytest.mark.asyncio
    async def test_status_handler_user_not_found(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /status handler when user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock no existing user
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_message.reply_text = AsyncMock()

        # Execute
        await user_handlers.status_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário não encontrado. Use /pay para assinar.")

    @pytest.mark.asyncio
    async def test_pay_handler_no_user_or_message(self, user_handlers):
        """Test /pay handler with missing user or message"""
        update = Mock(spec=Update)
        update.effective_user = None
        update.message = None
        context = Mock()

        # Should not raise exception, just return
        await user_handlers.pay_handler(update, context)

    # ===== RENEW HANDLER TESTS =====

    @pytest.mark.asyncio
    async def test_renew_handler_user_not_found(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /renew handler when user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock no existing user
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_message.reply_text = AsyncMock()

        # Execute
        await user_handlers.renew_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("Usuário não encontrado. Use /pay para assinar primeiro.")

    @pytest.mark.asyncio
    async def test_renew_handler_no_active_subscription(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /renew handler when user has no active subscription"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock user with inactive subscription
        mock_user = Mock()
        mock_user.status_assinatura = "inactive"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_message.reply_text = AsyncMock()

        # Execute
        await user_handlers.renew_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("Você não possui uma assinatura ativa. Use /pay para assinar.")

    @pytest.mark.asyncio
    async def test_renew_handler_expired_subscription(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /renew handler when subscription is expired"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock user with expired subscription
        mock_user = Mock()
        mock_user.status_assinatura = "active"
        # Set expiration date to past
        import datetime
        mock_user.data_expiracao = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user
        mock_message.reply_text = AsyncMock()

        # Execute
        await user_handlers.renew_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("Sua assinatura expirou. Use /pay para renovar.")

    @pytest.mark.asyncio
    @patch("src.handlers.user_handlers.Payment")
    async def test_renew_handler_successful_pix_payment(self, mock_payment_class, user_handlers, mock_telegram_user, mock_message, mock_db, mock_pixgo_service):
        """Test /renew handler with successful PIX payment creation"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock user with active, non-expired subscription
        mock_user = Mock()
        mock_user.id = 1
        mock_user.status_assinatura = "active"
        mock_user.username = "testuser"
        # Set future expiration date
        import datetime
        mock_user.data_expiracao = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user

        mock_message.reply_text = AsyncMock()

        # Mock PIX payment creation success
        mock_pixgo_service.create_payment.return_value = {
            "id": "pix_renew_123",
            "qr_code": "renew_qr_code_data"
        }
        mock_pixgo_service.get_qr_code.return_value = "RENEW_QR_CODE_DATA"

        # Execute
        await user_handlers.renew_handler(update, context)

        # Assert database operations
        # Check that Payment was instantiated with correct parameters
        mock_payment_class.assert_called_once_with(
            user_id=mock_user.id,
            pixgo_payment_id="pix_renew_123",
            amount=Config.SUBSCRIPTION_PRICE,
            payment_method="pix"
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Assert PIX service calls
        mock_pixgo_service.create_payment.assert_called_once_with(
            amount=Config.SUBSCRIPTION_PRICE,
            description="Renovação de Assinatura VIP - testuser",
            payer_info={"telegram_id": str(mock_telegram_user.id)}
        )
        mock_pixgo_service.get_qr_code.assert_called_once_with("pix_renew_123")

        # Assert message sent to user
        mock_message.reply_text.assert_called_once()
        response = mock_message.reply_text.call_args[0][0]
        assert "🔄 **Renovação de Assinatura**" in response
        assert f"R$ {Config.SUBSCRIPTION_PRICE:.2f}" in response
        assert "RENEW_QR_CODE_DATA" in response
        assert f"mais {Config.SUBSCRIPTION_DAYS} dias" in response

    @pytest.mark.asyncio
    async def test_renew_handler_pix_payment_fails_fallback_to_usdt(self, user_handlers, mock_telegram_user, mock_message, mock_db, mock_pixgo_service, mock_usdt_service):
        """Test /renew handler when PIX payment fails and falls back to USDT"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock user with active, non-expired subscription
        mock_user = Mock()
        mock_user.status_assinatura = "active"
        # Set future expiration date
        import datetime
        mock_user.data_expiracao = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user

        mock_message.reply_text = AsyncMock()

        # Mock PIX payment creation failure
        mock_pixgo_service.create_payment.return_value = None

        # Execute
        await user_handlers.renew_handler(update, context)

        # Assert USDT fallback
        mock_usdt_service.get_payment_instructions.assert_called_once_with(Config.SUBSCRIPTION_PRICE)

        # Assert message sent with USDT instructions
        mock_message.reply_text.assert_called_once_with(
            f"PIX indisponível. Use USDT para renovação:\nUSDT payment instructions"
        )

        # Assert no database operations for payment (since PIX failed)
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_renew_handler_no_user_or_message(self, user_handlers):
        """Test /renew handler with missing user or message"""
        update = Mock(spec=Update)
        update.effective_user = None
        update.message = None
        context = Mock()

        # Should not raise exception, just return
        await user_handlers.renew_handler(update, context)

    # ===== STATUS HANDLER TESTS =====

    def test_status_handler_success(self, user_handlers, mock_db, mock_telegram_user, mock_message):
        """Test successful status handler execution"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock database user
        mock_db_user = Mock()
        mock_db_user.status_assinatura = "ativo"
        mock_db_user.data_expiracao = Mock()
        mock_db_user.data_expiracao.strftime = Mock(return_value="31/12/2025")
        mock_db_user.is_banned = False
        mock_db_user.is_muted = False

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_db_user

        # Execute
        import asyncio
        asyncio.run(user_handlers.status_handler(update, context))

        # Assert
        mock_db.query.return_value.filter_by.assert_called_once()
        mock_message.reply_text.assert_called_once()
        # Check that the message contains expected status information
        call_args = mock_message.reply_text.call_args[0][0]
        assert "Status da Assinatura" in call_args
        assert "ativo" in call_args
        assert "31/12/2025" in call_args

    def test_status_handler_user_not_found(self, user_handlers, mock_db, mock_telegram_user, mock_message):
        """Test status handler when user is not found in database"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock user not found
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        import asyncio
        asyncio.run(user_handlers.status_handler(update, context))

        # Assert
        mock_message.reply_text.assert_called_once_with(
            "Usuário não encontrado. Certifique-se de ter iniciado uma conversa com o bot."
        )

    def test_status_handler_no_user_or_message(self, user_handlers):
        """Test status handler with missing user or message"""
        update = Mock(spec=Update)
        update.effective_user = None
        update.message = None
        context = Mock()

        # Should not raise exception, just return
        import asyncio
        asyncio.run(user_handlers.status_handler(update, context))

    @pytest.mark.asyncio
    async def test_help_handler_success(self, user_handlers, mock_message):
        """Test /help handler displays available commands"""
        # Setup
        update = Mock(spec=Update)
        update.message = mock_message
        context = Mock()

        # Execute
        await user_handlers.help_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once()
        help_response = mock_message.reply_text.call_args[0][0]
        
        # Check that help message contains expected commands
        assert "🤖 **Comandos Disponíveis**" in help_response
        assert "/pay" in help_response
        assert "/status" in help_response
        assert "/renew" in help_response
        assert "/help" in help_response
        assert "/invite" in help_response

    @pytest.mark.asyncio
    async def test_help_handler_no_message(self, user_handlers):
        """Test /help handler with no message (should not crash)"""
        # Setup
        update = Mock(spec=Update)
        update.message = None
        context = Mock()

        # Execute - should not raise exception
        await user_handlers.help_handler(update, context)

    def test_help_message_formatting(self, user_handlers, mock_message):
        """Test help message formatting and content"""
        # Setup
        update = Mock(spec=Update)
        update.message = mock_message
        context = Mock()

        # Execute
        import asyncio
        asyncio.run(user_handlers.help_handler(update, context))

        # Assert message formatting
        call_args = mock_message.reply_text.call_args
        message_text = call_args[0][0]
        parse_mode = call_args[1].get('parse_mode')
        
        # Check markdown formatting
        assert parse_mode == "Markdown"
        
        # Check message structure
        lines = [line.strip() for line in message_text.split('\n') if line.strip()]
        assert lines[0] == "🤖 **Comandos Disponíveis**"
        
        # Check that all commands are listed
        assert any("/pay" in line for line in lines)
        assert any("/status" in line for line in lines)
        assert any("/renew" in line for line in lines)
        assert any("/help" in line for line in lines)
        assert any("/invite" in line for line in lines)

    @pytest.mark.asyncio
    async def test_invite_handler_success(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /invite handler generates invite link for active user"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock active user
        mock_db_user = Mock()
        mock_db_user.status_assinatura = "ativo"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_db_user

        # Execute
        await user_handlers.invite_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once()
        response = mock_message.reply_text.call_args[0][0]

        # Check that invite message contains expected content
        assert "🎫 **Link de Convite**" in response
        assert "Seu link de convite exclusivo:" in response
        assert "https://t.me/" in response
        assert "start=invite_" in response
        assert "Rastreamento será implementado em breve" in response

    @pytest.mark.asyncio
    async def test_invite_handler_user_not_found(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /invite handler when user is not found in database"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock user not found
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        await user_handlers.invite_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with(
            "Usuário não encontrado. Use /pay para assinar primeiro."
        )

    @pytest.mark.asyncio
    async def test_invite_handler_inactive_subscription(self, user_handlers, mock_telegram_user, mock_message, mock_db):
        """Test /invite handler when user doesn't have active subscription"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        context = Mock()

        # Mock user with inactive subscription
        mock_db_user = Mock()
        mock_db_user.status_assinatura = "expirado"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_db_user

        # Execute
        await user_handlers.invite_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with(
            "Você precisa ter uma assinatura ativa para gerar links de convite."
        )

    @pytest.mark.asyncio
    async def test_invite_handler_no_user_or_message(self, user_handlers):
        """Test /invite handler with missing user or message"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = None
        update.message = None
        context = Mock()

        # Execute - should not raise exception
        await user_handlers.invite_handler(update, context)

    @pytest.mark.asyncio
    async def test_cancel_handler_success(self, user_handlers, mock_telegram_user, mock_message, mock_chat):
        """Test /cancel handler success case"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        # Mock database user with active subscription
        from src.models.user import User
        mock_db_user = Mock(spec=User)
        mock_db_user.status_assinatura = "active"
        mock_db_user.auto_renew = True
        user_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_db_user

        # Execute
        await user_handlers.cancel_handler(update, context)

        # Assert
        assert mock_db_user.auto_renew == False
        user_handlers.db.commit.assert_called_once()
        mock_message.reply_text.assert_called_once()
        response_text = mock_message.reply_text.call_args[0][0]
        assert "Renovação automática desabilitada com sucesso" in response_text

    @pytest.mark.asyncio
    async def test_cancel_handler_user_not_found(self, user_handlers, mock_telegram_user, mock_message, mock_chat):
        """Test /cancel handler when user is not found"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        # Mock user not found
        user_handlers.db.query.return_value.filter_by.return_value.first.return_value = None

        # Execute
        await user_handlers.cancel_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Usuário não encontrado. Use /start primeiro.")

    @pytest.mark.asyncio
    async def test_cancel_handler_no_active_subscription(self, user_handlers, mock_telegram_user, mock_message, mock_chat):
        """Test /cancel handler when user has no active subscription"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        # Mock database user with inactive subscription
        from src.models.user import User
        mock_db_user = Mock(spec=User)
        mock_db_user.status_assinatura = "inactive"
        user_handlers.db.query.return_value.filter_by.return_value.first.return_value = mock_db_user

        # Execute
        await user_handlers.cancel_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Você não possui uma assinatura ativa para cancelar.")

    @pytest.mark.asyncio
    async def test_cancel_handler_private_chat(self, user_handlers, mock_telegram_user, mock_message, mock_chat):
        """Test /cancel handler in private chat (should fail)"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        # Execute
        await user_handlers.cancel_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos de usuário só podem ser executados em grupos.")

    @pytest.mark.asyncio
    async def test_support_handler_success(self, user_handlers, mock_telegram_user, mock_message, mock_chat):
        """Test /support handler success case"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        # Execute
        await user_handlers.support_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once()
        response_text = mock_message.reply_text.call_args[0][0]
        assert "Suporte Técnico" in response_text
        assert "suporte@viptelegram.com" in response_text
        assert "@suporte_vip_bot" in response_text

    @pytest.mark.asyncio
    async def test_support_handler_private_chat(self, user_handlers, mock_telegram_user, mock_message, mock_chat):
        """Test /support handler in private chat (should fail)"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        # Execute
        await user_handlers.support_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos de usuário só podem ser executados em grupos.")

    @pytest.mark.asyncio
    async def test_info_handler_success(self, user_handlers, mock_telegram_user, mock_message, mock_chat):
        """Test /info handler success case"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        context = Mock()

        # Execute
        await user_handlers.info_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once()
        response_text = mock_message.reply_text.call_args[0][0]
        assert "Sobre o Grupo VIP Telegram" in response_text
        assert "acesso exclusivo a grupos VIP" in response_text

    @pytest.mark.asyncio
    async def test_info_handler_private_chat(self, user_handlers, mock_telegram_user, mock_message, mock_chat):
        """Test /info handler in private chat (should fail)"""
        # Setup
        update = Mock(spec=Update)
        update.effective_user = mock_telegram_user
        update.message = mock_message
        update.effective_chat = mock_chat
        mock_chat.type = "private"
        context = Mock()

        # Execute
        await user_handlers.info_handler(update, context)

        # Assert
        mock_message.reply_text.assert_called_once_with("❌ Comandos de usuário só podem ser executados em grupos.")
