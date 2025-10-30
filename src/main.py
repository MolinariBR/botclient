import asyncio
import logging
import sys
import os
import threading
import time

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ChatMemberHandler, filters
from telegram import Update

from handlers.admin_handlers import AdminHandlers
from handlers.user_handlers import UserHandlers
from services.mute_service import MuteService
from services.pixgo_service import PixGoService
from services.usdt_service import USDTService
from services.telegram_service import TelegramService
from services.logging_service import LoggingService
from utils.config import Config
from utils.logger import setup_logging
from utils.performance import performance_monitor


def start_performance_monitoring():
    """Start background performance monitoring"""
    def monitor_loop():
        while True:
            time.sleep(300)  # Log every 5 minutes
            try:
                performance_monitor.log_summary()
            except Exception as e:
                logging.error(f"Error logging performance summary: {e}")

    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    logging.info("Performance monitoring started")


def main():
    # Setup logging
    setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)

    # Start performance monitoring
    start_performance_monitoring()

    # Validate configuration
    errors = Config.validate()
    if errors:
        logging.error("Configuration errors:")
        for error in errors:
            logging.error(f"  - {error}")
        return

    # Database setup
    engine = create_engine(Config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Database session
    db = SessionLocal()

    # Services
    pixgo_service = PixGoService(Config.PIXGO_API_KEY, Config.PIXGO_BASE_URL)
    usdt_service = USDTService(Config.USDT_WALLET_ADDRESS)
    telegram_service = TelegramService(Config.TELEGRAM_TOKEN)
    mute_service = MuteService(db)
    logging_service = LoggingService()

    # Handlers
    user_handlers = UserHandlers(db, pixgo_service, usdt_service)
    admin_handlers = AdminHandlers(db, telegram_service, logging_service)

    # Telegram application with basic configuration
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # Log network diagnostic info
    logging.info("Bot configuration:")
    logging.info(f"  - Telegram token configured: {'Yes' if Config.TELEGRAM_TOKEN else 'No'}")
    logging.info(f"  - Database URL: {Config.DATABASE_URL}")
    logging.info("Starting bot with network error handling...")

    # Add handlers for different chat types to debug
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

    # Add chat member handler to track bot status in groups
    application.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))

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

    # Add test handler (will be overridden by specific handlers)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, test_handler))

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

    # Payment callbacks
    application.add_handler(CallbackQueryHandler(user_handlers.payment_callback_handler, pattern="^pay_"))

    # Admin commands
    application.add_handler(CommandHandler("add", admin_handlers.add_handler))
    application.add_handler(CommandHandler("addadmin", admin_handlers.addadmin_handler))
    application.add_handler(CommandHandler("register_group", admin_handlers.register_group_handler))
    application.add_handler(CommandHandler("group_id", admin_handlers.group_id_handler))
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
    application.add_handler(CommandHandler("logs", admin_handlers.logs_handler))
    application.add_handler(CommandHandler("admins", admin_handlers.admins_handler))
    application.add_handler(CommandHandler("settings", admin_handlers.settings_handler))
    application.add_handler(CommandHandler("backup", admin_handlers.backup_handler))
    application.add_handler(CommandHandler("restore", admin_handlers.restore_handler))

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
                # Check if webhook URL is configured
                webhook_url = os.getenv('WEBHOOK_URL')
                if webhook_url:
                    try:
                        logging.info(f"Setting webhook: {webhook_url}")
                        await application.bot.set_webhook(
                            url=webhook_url,
                            allowed_updates=["message", "callback_query", "chat_member"]
                        )
                        logging.info("✅ Webhook configured successfully")
                    except Exception as webhook_error:
                        logging.warning(f"Webhook setup failed: {webhook_error}, continuing with polling")

                # Start polling with error handling and optimized settings for Square Cloud
                try:
                    async with application:
                        await application.start()
                        logging.info("✅ Bot started successfully!")

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

    async def main_async():
        """Main async function that runs bot and mute service concurrently"""
        # Start mute service
        await mute_service.start()

        try:
            # Run bot
            await run_bot()
        except KeyboardInterrupt:
            logging.info("Received shutdown signal")
        finally:
            # Stop services gracefully
            try:
                await mute_service.stop()
                logging.info("✅ Services stopped gracefully")
            except Exception as e:
                logging.error(f"Error stopping services: {e}")

    # Run everything
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
