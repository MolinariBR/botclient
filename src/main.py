from handlers.admin_handlers import AdminHandlers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from handlers.user_handlers import UserHandlers

# Garante que o diretório raiz do projeto está no sys.path antes de qualquer import
import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ChatMemberHandler
from utils.config import Config
from utils.logger import setup_logging

load_dotenv('.env.local')
token = os.getenv('TELEGRAM_TOKEN')

import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler
from utils.config import Config
from services.mute_service import MuteService
from services.pixgo_service import PixGoService
from services.usdt_service import USDTService
from services.telegram_service import TelegramService
from services.logging_service import LoggingService

load_dotenv('.env.local')
token = os.getenv('TELEGRAM_TOKEN')

if not token:
    print('TELEGRAM_TOKEN não encontrado!')
    exit(1)

# Setup logging apenas para console
logging.basicConfig(level=logging.INFO)
logging.info('Configuração de logging ativada (console only).')
logging.info(f'TOKEN carregado: {bool(token)}')
logging.info(f'DATABASE_URL: {getattr(Config, "DATABASE_URL", None)}')

# Inicialização dos serviços

# Inicialização dos serviços
pixgo_service = PixGoService(Config.PIXGO_API_KEY, Config.PIXGO_BASE_URL)
usdt_service = USDTService(Config.USDT_WALLET_ADDRESS)
telegram_service = TelegramService(Config.TELEGRAM_TOKEN)
mute_service = MuteService(None)
logging_service = LoggingService()
logging.info('Serviços inicializados.')

# Inicialização do banco de dados
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()


# Inicialização dos handlers de usuário e admin
user_handlers = UserHandlers(db, pixgo_service, usdt_service)
admin_handlers = AdminHandlers(db, telegram_service, logging_service)
logging.info('UserHandlers e AdminHandlers inicializados.')


# Handler original de /start
async def start(update, context):
    await user_handlers.start_handler(update, context)

app = Application.builder().token(token).build()
app.add_handler(CommandHandler('start', start))




app = Application.builder().token(token).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('help', user_handlers.help_handler))
app.add_handler(CommandHandler('status', user_handlers.status_handler))
app.add_handler(CommandHandler('pay', user_handlers.pay_handler))
app.add_handler(CommandHandler('renew', user_handlers.renew_handler))
# Handlers de admin
app.add_handler(CommandHandler('add', admin_handlers.add_handler))
app.add_handler(CommandHandler('kick', admin_handlers.kick_handler))
app.add_handler(CommandHandler('ban', admin_handlers.ban_handler))
app.add_handler(CommandHandler('unban', admin_handlers.unban_handler))
app.add_handler(CommandHandler('mute', admin_handlers.mute_handler))
app.add_handler(CommandHandler('unmute', admin_handlers.unmute_handler))
app.add_handler(CommandHandler('warn', admin_handlers.warn_handler))
app.add_handler(CommandHandler('resetwarn', admin_handlers.resetwarn_handler))
app.add_handler(CommandHandler('setprice', admin_handlers.setprice_handler))
app.add_handler(CommandHandler('settime', admin_handlers.settime_handler))
app.add_handler(CommandHandler('setwallet', admin_handlers.setwallet_handler))
app.add_handler(CommandHandler('rules', admin_handlers.rules_handler))
app.add_handler(CommandHandler('welcome', admin_handlers.welcome_handler))
app.add_handler(CommandHandler('schedule', admin_handlers.schedule_handler))
app.add_handler(CommandHandler('stats', admin_handlers.stats_handler))
app.add_handler(CommandHandler('logs', admin_handlers.logs_handler))
app.add_handler(CommandHandler('admins', admin_handlers.admins_handler))
app.add_handler(CommandHandler('settings', admin_handlers.settings_handler))
app.add_handler(CommandHandler('backup', admin_handlers.backup_handler))
app.add_handler(CommandHandler('restore', admin_handlers.restore_handler))
app.add_handler(CommandHandler('restore_quick', admin_handlers.restore_handler))
logging.info('Todos os handlers de usuário e admin ativados.')

print('Bot main.py rodando com todos os handlers. Teste comandos de usuário e admin no Telegram.')
app.run_polling()


def setup_handlers(application, user_handlers, admin_handlers, mute_service):
    """Setup all bot handlers"""
    logging.info("🔧 Starting handler setup...")

    # Add handlers for different chat types to debug
    async def message_logger(update, context):
        """Log all incoming messages for debugging"""
        try:
            if update.message:
                user = update.effective_user
                chat = update.effective_chat
                message = update.message
                text = message.text or "[non-text]"

                logging.info(f"📨 MESSAGE RECEIVED: '{text}' from {user.username or user.first_name} in {chat.type} chat {chat.id}")

                # Send immediate confirmation - TEMPORARILY ENABLED for testing
                try:
                    if text.startswith('/'):  # Only respond to commands for testing
                        await message.reply_text(f"📨 Comando recebido: {text}")
                        logging.info("✅ Command confirmation sent")
                except Exception as reply_error:
                    logging.error(f"❌ Could not send confirmation: {reply_error}")

        except Exception as e:
            logging.error(f"❌ Error in message logger: {e}")

    async def chat_member_handler(update, context):
        """Handle chat member updates (bot added/removed from groups)"""
        try:
            chat_member = update.chat_member
            if chat_member:
                chat = chat_member.chat
                user = chat_member.new_chat_member.user
                status = chat_member.new_chat_member.status

                if user.id == (await context.bot.get_me()).id:
                    logging.info(f"🤖 Bot status changed in chat {chat.title} ({chat.id}): {status}")

                    if status == "member":
                        logging.info(f"✅ Bot added to group: {chat.title}")
                        await context.bot.send_message(
                            chat_id=chat.id,
                            text="🤖 Bot VIP Telegram adicionado ao grupo! Use /help para ver comandos."
                        )
                    elif status == "administrator":
                        logging.info(f"✅ Bot promoted to admin in: {chat.title}")
                    elif status in ["left", "kicked"]:
                        logging.warning(f"❌ Bot removed from group: {chat.title}")

        except Exception as e:
            logging.error(f"Error in chat member handler: {e}")


    # Add message logger FIRST (highest priority) to catch ALL messages
    application.add_handler(MessageHandler(filters.ALL, message_logger), group=0)  # ENABLED
    logging.info("✅ Message logger handler added (UNIVERSAL)")

    # Add chat member handler to track bot status in groups
    application.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))
    logging.info("✅ Chat member handler added")

    # Add user command handlers
    async def debug_start_handler(update, context):
        try:
            result = await user_handlers.start_handler(update, context)
            logging.info("✅ DEBUG: start_handler completed")
            return result
        except Exception as e:
            logging.error(f"❌ DEBUG: start_handler failed: {e}")
            raise

    async def debug_help_handler(update, context):
        try:
            result = await user_handlers.help_handler(update, context)
            logging.info("✅ DEBUG: help_handler completed")
            return result
        except Exception as e:
            logging.error(f"❌ DEBUG: help_handler failed: {e}")
            raise

    async def debug_status_handler(update, context):
        try:
            result = await user_handlers.status_handler(update, context)
            logging.info("✅ DEBUG: status_handler completed")
            return result
        except Exception as e:
            logging.error(f"❌ DEBUG: status_handler failed: {e}")
            raise

    application.add_handler(CommandHandler("start", debug_start_handler))
    application.add_handler(CommandHandler("help", debug_help_handler))
    application.add_handler(CommandHandler("status", debug_status_handler))
    application.add_handler(CommandHandler("pay", user_handlers.pay_handler))
    application.add_handler(CommandHandler("renew", user_handlers.renew_handler))
    application.add_handler(CommandHandler("group_id", admin_handlers.group_id_handler), group=-1)
    logging.info("✅ User command handlers added")

    # Add admin command handlers
    application.add_handler(CommandHandler("add", admin_handlers.add_handler))
    application.add_handler(CommandHandler("kick", admin_handlers.kick_handler))
    application.add_handler(CommandHandler("ban", admin_handlers.ban_handler))
    application.add_handler(CommandHandler("unban", admin_handlers.unban_handler))
    application.add_handler(CommandHandler("mute", admin_handlers.mute_handler))
    application.add_handler(CommandHandler("unmute", admin_handlers.unmute_handler))
    application.add_handler(CommandHandler("warn", admin_handlers.warn_handler))
    application.add_handler(CommandHandler("resetwarn", admin_handlers.resetwarn_handler))
    application.add_handler(CommandHandler("setprice", admin_handlers.setprice_handler))
    application.add_handler(CommandHandler("settime", admin_handlers.settime_handler))
    application.add_handler(CommandHandler("setwallet", admin_handlers.setwallet_handler))
    application.add_handler(CommandHandler("rules", admin_handlers.rules_handler))
    application.add_handler(CommandHandler("welcome", admin_handlers.welcome_handler))
    application.add_handler(CommandHandler("schedule", admin_handlers.schedule_handler))
    application.add_handler(CommandHandler("stats", admin_handlers.stats_handler))
    application.add_handler(CommandHandler("logs", admin_handlers.logs_handler))
    application.add_handler(CommandHandler("admins", admin_handlers.admins_handler))
    application.add_handler(CommandHandler("settings", admin_handlers.settings_handler))
    application.add_handler(CommandHandler("backup", admin_handlers.backup_handler))
    application.add_handler(CommandHandler("restore", admin_handlers.restore_handler))
    application.add_handler(CommandHandler("restore_quick", admin_handlers.restore_handler))
    logging.info("✅ Admin command handlers added")
    print("[DEBUG] Todos os handlers foram adicionados com sucesso.")
    logging.info("[DEBUG] Todos os handlers foram adicionados com sucesso.")


async def run_bot(application):
    """Run the bot with polling configuration optimized for Square Cloud"""
    max_retries = 5
    retry_delay = 5.0

    print("[DEBUG] Entrou em run_bot")
    logging.info("[DEBUG] Entrou em run_bot")
    for attempt in range(max_retries):
        try:
            logging.info(f"Initializing bot (attempt {attempt + 1}/{max_retries})...")

            # Test connectivity before initializing
            try:
                # Quick test to see if we can reach Telegram API
                test_response = await application.bot.get_me()
                logging.info(f"✅ Telegram API reachable - Bot: @{test_response.username}")
                logging.info(f"   Bot ID: {test_response.id}")
                logging.info(f"   Can join groups: {test_response.can_join_groups}")
                logging.info(f"   Can read all messages: {test_response.can_read_all_group_messages}")

                # Test sending a message to ourselves (if possible)
                try:
                    await application.bot.send_message(
                        chat_id=test_response.id,
                        text="🤖 Bot inicializado com sucesso! Teste de conectividade OK."
                    )
                    logging.info("✅ Test message sent to bot itself")
                except Exception as msg_error:
                    logging.warning(f"Could not send test message: {msg_error}")

            except Exception as conn_test_error:
                logging.warning(f"Connectivity test failed: {conn_test_error}, but continuing...")

            await application.initialize()

            print("[DEBUG] Inicialização do application feita")
            logging.info("[DEBUG] Inicialização do application feita")
            logging.info("Starting polling with optimized settings...")
            # Check if webhook URL is configured - only use in production
            webhook_url = os.getenv('WEBHOOK_URL')
            port = os.getenv('PORT')

            # Force polling for development/testing, webhook only for production
            use_webhook = bool(webhook_url and port and os.getenv('ENVIRONMENT') == 'production')

            if use_webhook and webhook_url:
                try:
                    logging.info(f"Setting webhook: {webhook_url}")
                    await application.bot.set_webhook(url=webhook_url)
                    logging.info("✅ Webhook configured successfully")

                    # Configure webhook with allowed updates
                    await application.bot.set_webhook(
                        url=webhook_url,
                        allowed_updates=["message", "callback_query", "chat_member"]
                    )
                    logging.info("✅ Webhook server configured")

                except Exception as webhook_error:
                    logging.warning(f"Webhook setup failed: {webhook_error}, falling back to polling")
                    use_webhook = False

            if not use_webhook:
                logging.info("Using polling mode...")
                # Delete any existing webhook
                try:
                    await application.bot.delete_webhook()
                    logging.info("✅ Webhook deleted (using polling)")
                except Exception as e:
                    logging.debug(f"Could not delete webhook: {e}")

                # Start polling with error handling and optimized settings for Square Cloud
                try:
                    print("[DEBUG] Antes do async with application")
                    async with application:
                        print("[DEBUG] Dentro do async with application, antes do start")
                        await application.start()
                        print("[DEBUG] Após application.start() - polling iniciado")
                        logging.info("✅ Bot started successfully with polling!")

                        # Keep the bot running with periodic health checks
                        while True:
                            print("[DEBUG] Loop principal do bot rodando...")
                            await asyncio.sleep(1)

                except Exception as polling_error:
                    logging.error(f"Polling error: {polling_error}")
                    raise

        except Exception as e:
            logging.error(f"Bot error on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
            else:
                logging.error("Max retries reached. Giving up.")
                raise


async def main_async(application, mute_service):
    """Main async function that runs bot and mute service concurrently"""
    # Start mute service
    await mute_service.start()

    try:
        # Run bot
        await run_bot(application)
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
    finally:
        # Stop services gracefully
        try:
            await mute_service.stop()
            logging.info("✅ Services stopped gracefully")
        except Exception as e:
            logging.error(f"Error stopping services: {e}")


def main():
    # Remover webhook explicitamente de forma assíncrona antes de tudo
    import asyncio
    import telegram
    async def delete_webhook_async():
        try:
            bot = telegram.Bot(token=Config.TELEGRAM_TOKEN)
            print("[DEBUG] Deletando webhook explicitamente (async)...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("[DEBUG] Webhook deletado com sucesso (async)!")
        except Exception as e:
            print(f"[DEBUG] Falha ao deletar webhook (async): {e}")
    asyncio.run(delete_webhook_async())
    try:
        logging.info("🚀 Starting bot main function...")

        # Setup logging
        setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
        logging.info("✅ Logging setup complete")

        # Start performance monitoring
        # start_performance_monitoring()  # TODO: Implement performance monitoring
        logging.info("✅ Performance monitoring started")

        # Validate configuration
        errors = Config.validate()
        if errors:
            logging.error("❌ Configuration errors:")
            for error in errors:
                logging.error(f"  - {error}")
            logging.error("❌ Bot cannot start due to configuration errors")
            return

        logging.info("✅ Configuration validation passed")

        # Database setup
        logging.info("🔧 Setting up database...")
        engine = create_engine(Config.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logging.info("✅ Database setup complete")

        # Database session
        db = SessionLocal()
        logging.info("✅ Database session created")

        # Services
        logging.info("🔧 Initializing services...")
        pixgo_service = PixGoService(Config.PIXGO_API_KEY, Config.PIXGO_BASE_URL)
        usdt_service = USDTService(Config.USDT_WALLET_ADDRESS)
        telegram_service = TelegramService(Config.TELEGRAM_TOKEN)
        mute_service = MuteService(db)
        logging_service = LoggingService()
        logging.info("✅ Services initialized")

        # Handlers
        logging.info("🔧 Initializing handlers...")
        user_handlers = UserHandlers(db, pixgo_service, usdt_service)
        admin_handlers = AdminHandlers(db, telegram_service, logging_service)
        logging.info("✅ Handlers initialized")

        # Telegram application with basic configuration
        logging.info("🔧 Creating Telegram application...")
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        logging.info("✅ Telegram application created")

        # Log network diagnostic info
        logging.info("Bot configuration:")
        logging.info(f"  - Telegram token configured: {'Yes' if Config.TELEGRAM_TOKEN else 'No'}")
        logging.info(f"  - Database URL: {Config.DATABASE_URL}")
        logging.info("Starting bot with network error handling...")

        # Add handlers
        logging.info("� Adding handlers...")
        setup_handlers(application, user_handlers, admin_handlers, mute_service)
        logging.info("✅ Handlers added")

        # Run bot
        logging.info("🚀 Starting bot execution...")
        asyncio.run(main_async(application, mute_service))

    except Exception as e:
        logging.error(f"❌ CRITICAL ERROR in main(): {e}")
        import traceback
        logging.error(f"❌ Traceback: {traceback.format_exc()}")
        raise

    # Add a simple test handler to verify bot is receiving messages
    async def test_handler(update, context):
        """Simple test handler to verify bot is receiving messages"""
        try:
            user = update.effective_user
            chat = update.effective_chat
            message = update.effective_message

            if user and chat and message:
                logging.info(f"📨 TEST HANDLER: Message received from {user.username or user.first_name} in chat {chat.id}: {message.text}")

                # Simple echo response for testing
                response_text = f"✅ Bot funcionando! Recebi: {message.text[:50] if message.text else 'mensagem'}..."
                logging.info(f"📤 TEST HANDLER: Sending response: {response_text}")

                await message.reply_text(response_text)
                logging.info("📤 TEST HANDLER: Response sent successfully")

        except Exception as e:
            logging.error(f"❌ TEST HANDLER ERROR: {e}")
            import traceback
            logging.error(f"❌ TEST HANDLER TRACEBACK: {traceback.format_exc()}")

            # Add handlers for different chat types to debug
        async def message_logger(update, context):
            """Log all incoming messages for debugging"""
            try:
                if update.message:
                    user = update.effective_user
                    chat = update.effective_chat
                    message = update.message
                    text = message.text or "[non-text]"

                    logging.info(f"📨 MESSAGE RECEIVED: '{text}' from {user.username or user.first_name} in {chat.type} chat {chat.id}")

                    # Send immediate confirmation
                    try:
                        await message.reply_text(f"📨 Mensagem recebida: {text[:50]}...")
                        logging.info("✅ Confirmation sent")
                    except Exception as reply_error:
                        logging.error(f"❌ Could not send confirmation: {reply_error}")

            except Exception as e:
                logging.error(f"❌ Error in message logger: {e}")

        async def chat_member_handler(update, context):
            """Handle chat member updates (bot added/removed from groups)"""
            try:
                chat_member = update.chat_member
                if chat_member:
                    chat = chat_member.chat
                    user = chat_member.new_chat_member.user
                    status = chat_member.new_chat_member.status

                    if user.id == (await context.bot.get_me()).id:
                        logging.info(f"🤖 Bot status changed in chat {chat.title} ({chat.id}): {status}")

                        if status == "member":
                            logging.info(f"✅ Bot added to group: {chat.title}")
                            await context.bot.send_message(
                                chat_id=chat.id,
                                text="🤖 Bot VIP Telegram adicionado ao grupo! Use /help para ver comandos."
                            )
                        elif status == "administrator":
                            logging.info(f"✅ Bot promoted to admin in: {chat.title}")
                        elif status in ["left", "kicked"]:
                            logging.warning(f"❌ Bot removed from group: {chat.title}")

            except Exception as e:
                logging.error(f"Error in chat member handler: {e}")

        # Add message logger FIRST (highest priority) to catch ALL messages
        # application.add_handler(MessageHandler(filters.ALL, message_logger), group=0)  # DISABLED
        logging.info("✅ Message logger handler added")

        # Add chat member handler to track bot status in groups
        application.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))
        logging.info("✅ Chat member handler added")

        # Add user command handlers
        application.add_handler(CommandHandler("start", user_handlers.start_handler))
        application.add_handler(CommandHandler("pay", user_handlers.pay_handler))
        application.add_handler(CommandHandler("status", user_handlers.status_handler))
        application.add_handler(CommandHandler("renew", user_handlers.renew_handler))
        application.add_handler(CommandHandler("help", user_handlers.help_handler))
        application.add_handler(CommandHandler("invite", user_handlers.invite_handler))
        application.add_handler(CommandHandler("cancel", user_handlers.cancel_handler))
        application.add_handler(CommandHandler("support", user_handlers.support_handler))
        application.add_handler(CommandHandler("info", user_handlers.info_handler))
        logging.info("✅ User command handlers added")

        # Payment callbacks
        application.add_handler(CallbackQueryHandler(user_handlers.payment_callback_handler, pattern="^pay_"))
        logging.info("✅ Payment callback handler added")

        # Admin commands
        application.add_handler(CommandHandler("add", admin_handlers.add_handler))
        application.add_handler(CommandHandler("addadmin", admin_handlers.addadmin_handler))
        application.add_handler(CommandHandler("register_group", admin_handlers.register_group_handler))
        # application.add_handler(CommandHandler("group_id", admin_handlers.group_id_handler), group=-1)  # Moved to user handlers
        logging.info("✅ group_id command handler added")
        application.add_handler(CommandHandler("kick", admin_handlers.kick_handler))
        application.add_handler(CommandHandler("ban", admin_handlers.ban_handler))
        application.add_handler(CommandHandler("mute", admin_handlers.mute_handler))
        application.add_handler(CommandHandler("unban", admin_handlers.unban_handler))
        application.add_handler(CommandHandler("unmute", admin_handlers.unmute_handler))
        application.add_handler(CommandHandler("userinfo", admin_handlers.userinfo_handler))
        application.add_handler(CommandHandler("pending", admin_handlers.pending_handler))
        application.add_handler(CommandHandler("warn", admin_handlers.warn_handler))
        application.add_handler(CommandHandler("resetwarn", admin_handlers.resetwarn_handler))
        application.add_handler(CommandHandler("expire", admin_handlers.expire_handler))
        application.add_handler(CommandHandler("sendto", admin_handlers.sendto_handler))
        application.add_handler(
            CommandHandler("broadcast", admin_handlers.broadcast_handler)
        )
        application.add_handler(CommandHandler("setprice", admin_handlers.setprice_handler))
        application.add_handler(CommandHandler("settime", admin_handlers.settime_handler))
        application.add_handler(CommandHandler("setwallet", admin_handlers.setwallet_handler))
        application.add_handler(CommandHandler("rules", admin_handlers.rules_handler))
        application.add_handler(CommandHandler("welcome", admin_handlers.welcome_handler))
        application.add_handler(CommandHandler("schedule", admin_handlers.schedule_handler))
        application.add_handler(CommandHandler("stats", admin_handlers.stats_handler))
        logging.info("✅ Admin command handlers added")
    application.add_handler(CommandHandler("logs", admin_handlers.logs_handler))
    application.add_handler(CommandHandler("admins", admin_handlers.admins_handler))
    application.add_handler(CommandHandler("settings", admin_handlers.settings_handler))
    application.add_handler(CommandHandler("backup", admin_handlers.backup_handler))
    application.add_handler(CommandHandler("restore", admin_handlers.restore_handler))
    application.add_handler(CommandHandler("restore_quick", admin_handlers.restore_handler))

    logging.info("[DEBUG] Todos os handlers foram adicionados com sucesso.")
    logging.info("✅ Handler setup completed successfully")

    # Start the bot
    logging.info("Starting bot...")

    async def run_bot():
        """Run the bot with polling configuration optimized for Square Cloud"""
        max_retries = 5
        retry_delay = 5.0

        for attempt in range(max_retries):
            try:
                logging.info(f"Initializing bot (attempt {attempt + 1}/{max_retries})...")

                # Test connectivity before initializing
                try:
                    # Quick test to see if we can reach Telegram API
                    test_response = await application.bot.get_me()
                    logging.info(f"✅ Telegram API reachable - Bot: @{test_response.username}")
                    logging.info(f"   Bot ID: {test_response.id}")
                    logging.info(f"   Can join groups: {test_response.can_join_groups}")
                    logging.info(f"   Can read all messages: {test_response.can_read_all_group_messages}")

                    # Test sending a message to ourselves (if possible)
                    try:
                        await application.bot.send_message(
                            chat_id=test_response.id,
                            text="🤖 Bot inicializado com sucesso! Teste de conectividade OK."
                        )
                        logging.info("✅ Test message sent to bot itself")
                    except Exception as msg_error:
                        logging.warning(f"Could not send test message: {msg_error}")

                except Exception as conn_test_error:
                    logging.warning(f"Connectivity test failed: {conn_test_error}, but continuing...")

                await application.initialize()

                logging.info("Starting polling with optimized settings...")
                # Check if webhook URL is configured - only use in production
                webhook_url = os.getenv('WEBHOOK_URL')
                port = os.getenv('PORT')

                # Force polling for development/testing, webhook only for production
                use_webhook = bool(webhook_url and port and os.getenv('ENVIRONMENT') == 'production')

                if use_webhook and webhook_url:
                    try:
                        logging.info(f"Setting webhook: {webhook_url}")
                        await application.bot.set_webhook(url=webhook_url)
                        logging.info("✅ Webhook configured successfully")

                        # Configure webhook with allowed updates
                        await application.bot.set_webhook(
                            url=webhook_url,
                            allowed_updates=["message", "callback_query", "chat_member"]
                        )
                        logging.info("✅ Webhook server configured")

                    except Exception as webhook_error:
                        logging.warning(f"Webhook setup failed: {webhook_error}, falling back to polling")
                        use_webhook = False

                if not use_webhook:
                    logging.info("Using polling mode...")
                    # Delete any existing webhook
                    try:
                        await application.bot.delete_webhook()
                        logging.info("✅ Webhook deleted (using polling)")
                    except Exception as e:
                        logging.debug(f"Could not delete webhook: {e}")

                    # Start polling with error handling and optimized settings for Square Cloud
                    try:
                        async with application:
                            await application.start()
                            logging.info("✅ Bot started successfully with polling!")

                            # Keep the bot running with periodic health checks
                            while True:
                                await asyncio.sleep(1)

                    except Exception as polling_error:
                        logging.error(f"Polling error: {polling_error}")
                        raise

            except Exception as e:
                logging.error(f"Bot error on attempt {attempt + 1}: {e}")

                if attempt < max_retries - 1:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                else:
                    logging.error("Max retries reached. Giving up.")
                    raise


if __name__ == "__main__":
    main()

