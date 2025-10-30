import os
import logging

from dotenv import load_dotenv

# Setup basic logging for config loading
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from multiple sources
logger.info("Loading configuration from environment variables...")

# Try loading from .env first
env_loaded = load_dotenv()
if env_loaded:
    logger.info("Loaded configuration from .env file")
else:
    logger.info("No .env file found, trying .env.deploy...")
    # Try loading from .env.deploy
    env_deploy_loaded = load_dotenv('.env.deploy')
    if env_deploy_loaded:
        logger.info("Loaded configuration from .env.deploy file")
    else:
        logger.warning("No .env or .env.deploy file found")

logger.info("Environment variables loaded, validating configuration...")


class Config:
    # Telegram
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///botclient.db")

    # PixGo API
    PIXGO_API_KEY: str = os.getenv("PIXGO_API_KEY", "")
    PIXGO_BASE_URL: str = os.getenv("PIXGO_BASE_URL", "https://api.pixgo.com")

    # USDT
    USDT_WALLET_ADDRESS: str = os.getenv("USDT_WALLET_ADDRESS", "")

    # Bot settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")

    # Subscription settings
    SUBSCRIPTION_PRICE: float = float(os.getenv("SUBSCRIPTION_PRICE", "10.0"))
    SUBSCRIPTION_DAYS: int = int(os.getenv("SUBSCRIPTION_DAYS", "30"))

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration"""
        errors = []

        # Log configuration status (without exposing sensitive data)
        logger.info(f"TELEGRAM_TOKEN configured: {'Yes' if cls.TELEGRAM_TOKEN else 'No'}")
        logger.info(f"PIXGO_API_KEY configured: {'Yes' if cls.PIXGO_API_KEY else 'No'}")
        logger.info(f"USDT_WALLET_ADDRESS configured: {'Yes' if cls.USDT_WALLET_ADDRESS else 'No'}")
        logger.info(f"DATABASE_URL: {cls.DATABASE_URL}")
        logger.info(f"SUBSCRIPTION_PRICE: {cls.SUBSCRIPTION_PRICE}")
        logger.info(f"SUBSCRIPTION_DAYS: {cls.SUBSCRIPTION_DAYS}")

        if not cls.TELEGRAM_TOKEN:
            errors.append("TELEGRAM_TOKEN is required")
        if not cls.PIXGO_API_KEY:
            errors.append("PIXGO_API_KEY is required")
        if not cls.USDT_WALLET_ADDRESS:
            errors.append("USDT_WALLET_ADDRESS is required")
        return errors
