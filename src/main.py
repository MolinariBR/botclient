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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

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

    # Telegram application
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()

    # User commands
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
        """Run the telegram bot"""
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        # Keep the bot running
        while True:
            await asyncio.sleep(1)

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
            # Stop mute service
            await mute_service.stop()
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

    # Run everything
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
