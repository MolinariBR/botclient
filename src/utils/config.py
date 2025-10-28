import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
        if not cls.TELEGRAM_TOKEN:
            errors.append("TELEGRAM_TOKEN is required")
        if not cls.PIXGO_API_KEY:
            errors.append("PIXGO_API_KEY is required")
        if not cls.USDT_WALLET_ADDRESS:
            errors.append("USDT_WALLET_ADDRESS is required")
        return errors
