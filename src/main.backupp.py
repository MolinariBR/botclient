# Garante que o diretório raiz do projeto está no sys.path antes de qualquer import
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("DEBUG: Executando main.py REFATORADO - Versão limpa")

# Built-in imports
import os
import sys
import asyncio
import traceback
import logging

# External imports
import telegram
import httpx
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ChatMemberHandler

# Local imports
from utils.config import Config
from utils.logger import setup_logging
from handlers.admin_handlers import AdminHandlers
from handlers.user_handlers import UserHandlers
from services.mute_service import MuteService
from services.pixgo_service import PixGoService
from services.usdt_service import USDTService
from services.telegram_service import TelegramService
from services.logging_service import LoggingService

# Load environment variables
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


def get_db():
    """Centralized database setup"""
    engine = create_engine(Config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_services(db):
    """Initialize all services"""
    return {
        "pixgo": PixGoService(Config.PIXGO_API_KEY, Config.PIXGO_BASE_URL),
        "usdt": USDTService(Config.USDT_WALLET_ADDRESS),
        "telegram": TelegramService(Config.TELEGRAM_TOKEN),
        "mute": MuteService(db),
        "logging": LoggingService(),
    }


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

                # DISABLED: Send immediate confirmation - was interfering with command handlers
                # try:
                #     if text.startswith('/'):  # Only respond to commands for testing
                #         await message.reply_text(f"📨 Comando recebido: {text}")
                #         logging.info("✅ Command confirmation sent")
                # except Exception as reply_error:
                #     logging.error(f"❌ Could not send confirmation: {reply_error}")

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
    logging.info("✅ Message logger handler added (UNIVERSAL) - should log ALL messages")

    # Add chat member handler to track bot status in groups
    application.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))
    logging.info("✅ Chat member handler added")

    # Add user command handlers
    logging.info("🔧 Adding user command handlers...")
    application.add_handler(CommandHandler("start", user_handlers.start_handler))
    application.add_handler(CommandHandler("help", user_handlers.help_handler))
    application.add_handler(CommandHandler("status", user_handlers.status_handler))
    application.add_handler(CommandHandler("pay", user_handlers.pay_handler))
    application.add_handler(CommandHandler("renew", user_handlers.renew_handler))
    application.add_handler(CommandHandler("group_id", admin_handlers.group_id_handler), group=-10)
    logging.info("✅ User command handlers added")

    # Add test handler for debugging
    async def test_group_handler(update, context):
        try:
            logging.info("🧪 TEST_GROUP_HANDLER: Function called!")
            message = update.message
            if message and message.text:
                logging.info(f"🧪 TEST GROUP HANDLER: Received '{message.text}'")
                await message.reply_text(f"🧪 Teste: Recebi '{message.text}'")
                logging.info("🧪 TEST GROUP HANDLER: Response sent successfully")
        except Exception as e:
            logging.error(f"🧪 TEST GROUP HANDLER ERROR: {e}")
            logging.error(f"🧪 TEST GROUP HANDLER TRACEBACK: {traceback.format_exc()}")

    application.add_handler(CommandHandler("test_group", test_group_handler), group=-10)
    logging.info("✅ Test group handler added")

    # Add a simple group message responder for testing
    async def group_message_test(update, context):
        try:
            message = update.message
            if message and message.chat.type in ['group', 'supergroup']:
                # Only respond to messages that start with "TEST:"
                if message.text and message.text.upper().startswith("TEST:"):
                    logging.info(f"🎯 GROUP TEST: Received '{message.text}' in group {message.chat.id}")
                    await message.reply_text(f"🎯 Grupo detectado! ID: {message.chat.id}")
                    logging.info("🎯 GROUP TEST: Response sent")
        except Exception as e:
            logging.error(f"🎯 GROUP TEST ERROR: {e}")

    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, group_message_test), group=-5)
    logging.info("✅ Group message test handler added")

    # Add a catch-all group handler for debugging
    async def catch_all_groups(update, context):
        try:
            message = update.message
            if message and message.chat.type in ['group', 'supergroup']:
                logging.info(f"🎣 CATCH-ALL: Message in group {message.chat.id}: '{message.text}'")
                # Don't respond to avoid spam, just log
        except Exception as e:
            logging.error(f"🎣 CATCH-ALL ERROR: {e}")

    application.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, catch_all_groups), group=100)  # Lowest priority
    logging.info("✅ Catch-all group handler added")

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
    application.add_handler(CommandHandler("register_group", admin_handlers.register_group_handler))
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
                logging.info("🔗 Testing Telegram API connectivity...")
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
                        text="🤖 Bot inicializado com sucesso! Sistema de recuperação de rede ativo."
                    )
                    logging.info("✅ Test message sent to bot itself")
                except Exception as msg_error:
                    logging.warning(f"⚠️ Could not send test message: {msg_error}")

            except Exception as conn_test_error:
                logging.error(f"❌ CRITICAL: Cannot connect to Telegram API: {conn_test_error}")
                logging.error("❌ Bot cannot start without API connectivity")
                raise conn_test_error

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

                # Start polling with ROBUST error handling for Square Cloud network issues
                try:
                    logging.info("🚀 Starting ROBUST polling mode with network error recovery...")
                    logging.info("🔧 Initializing application...")

                    # Custom polling implementation with better error handling
                    await application.initialize()
                    await application.start()
                    logging.info("✅ Bot started successfully with robust polling!")
                    logging.info("🔄 Starting main polling loop...")

                    # Custom polling loop with error recovery
                    consecutive_errors = 0
                    max_consecutive_errors = 10
                    base_delay = 1.0
                    max_delay = 60.0
                    poll_count = 0

                    logging.info("🔄 Starting custom polling loop...")
                    while True:
                        poll_count += 1
                        logging.debug(f"🔄 Poll cycle #{poll_count} starting...")

                        try:
                            # Process updates with timeout
                            logging.debug("📡 Requesting updates from Telegram...")
                            async with asyncio.timeout(30):  # 30 second timeout for get_updates
                                updates = await application.bot.get_updates(
                                    timeout=25,  # Shorter than our timeout
                                    allowed_updates=["message", "callback_query", "chat_member"]
                                )

                            logging.debug(f"📡 Received {len(updates)} updates from Telegram")

                            # Process updates if any
                            if updates:
                                logging.info(f"📨 Processing {len(updates)} updates")
                                for update in updates:
                                    try:
                                        logging.debug(f"📨 Processing update: {update.update_id}")
                                        await application.process_update(update)
                                        logging.debug(f"✅ Update {update.update_id} processed successfully")
                                    except Exception as process_error:
                                        logging.error(f"❌ Error processing update {update.update_id}: {process_error}")
                                consecutive_errors = 0  # Reset error counter on success
                            else:
                                logging.debug("📡 No updates received (normal)")

                            # Small delay between polling cycles
                            await asyncio.sleep(0.1)

                        except asyncio.TimeoutError:
                            # Timeout is normal, just continue
                            logging.debug("⏰ Polling timeout (normal - no updates)")
                            consecutive_errors = 0
                            await asyncio.sleep(0.1)

                        except (telegram.error.NetworkError, httpx.ReadError, httpx.ConnectError) as network_error:
                            consecutive_errors += 1
                            delay = min(base_delay * (2 ** consecutive_errors), max_delay)

                            logging.warning(f"🌐 Network error #{consecutive_errors}: {network_error}")
                            logging.warning(f"   Retrying in {delay:.1f} seconds...")

                            if consecutive_errors >= max_consecutive_errors:
                                logging.error(f"💀 Too many consecutive network errors ({consecutive_errors}). Restarting bot...")
                                raise network_error

                            await asyncio.sleep(delay)

                        except Exception as update_error:
                            logging.error(f"❌ Unexpected polling error: {update_error}")
                            logging.error(f"   Error type: {type(update_error)}")
                            # Continue processing other updates
                            await asyncio.sleep(1)

                except Exception as polling_error:
                    logging.error(f"❌ Polling setup error: {polling_error}")
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
    # Setup logging
    setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
    logging.info("✅ Logging setup complete")

    # Validate configuration
    errors = Config.validate()
    if errors:
        logging.error("❌ Configuration errors:")
        for error in errors:
            logging.error(f"  - {error}")
        logging.error("❌ Bot cannot start due to configuration errors")
        return

    logging.info("✅ Configuration validation passed")

    # Database and services
    db = get_db()
    services = init_services(db)

    # Handlers
    user_handlers = UserHandlers(db, services["pixgo"], services["usdt"])
    admin_handlers = AdminHandlers(db, services["telegram"], services["logging"])

    # Telegram application
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # Add handlers
    setup_handlers(application, user_handlers, admin_handlers, services["mute"])

    # Run bot
    asyncio.run(main_async(application, services["mute"]))


if __name__ == "__main__":
    main()

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
    # Setup logging
    setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
    logging.info("✅ Logging setup complete")

    # Validate configuration
    errors = Config.validate()
    if errors:
        logging.error("❌ Configuration errors:")
        for error in errors:
            logging.error(f"  - {error}")
        logging.error("❌ Bot cannot start due to configuration errors")
        return

    logging.info("✅ Configuration validation passed")

    # Database and services
    db = get_db()
    services = init_services(db)

    # Handlers
    user_handlers = UserHandlers(db, services["pixgo"], services["usdt"])
    admin_handlers = AdminHandlers(db, services["telegram"], services["logging"])

    # Telegram application
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # Add handlers
    setup_handlers(application, user_handlers, admin_handlers, services["mute"])

    # Run bot
    asyncio.run(main_async(application, services["mute"]))


if __name__ == "__main__":
    main()

