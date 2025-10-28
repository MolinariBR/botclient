import logging

from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.token = token

    async def send_message(self, chat_id: int, text: str) -> bool:
        """Send a message to a chat"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=text)
            return True
        except TelegramError as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return False

    async def get_chat_member(self, chat_id: int, user_id: int):
        """Get chat member information"""
        try:
            return await self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        except TelegramError as e:
            logger.error(f"Failed to get chat member {user_id} in {chat_id}: {e}")
            return None

    async def kick_chat_member(self, chat_id: int, user_id: int) -> bool:
        """Kick a user from chat"""
        try:
            await self.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await self.bot.unban_chat_member(
                chat_id=chat_id, user_id=user_id
            )  # Unban to allow rejoin
            return True
        except TelegramError as e:
            logger.error(f"Failed to kick user {user_id} from {chat_id}: {e}")
            return False

    async def ban_chat_member(self, chat_id: int, user_id: int) -> bool:
        """Ban a user from chat"""
        try:
            await self.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            return True
        except TelegramError as e:
            logger.error(f"Failed to ban user {user_id} from {chat_id}: {e}")
            return False

    async def create_chat_invite_link(self, chat_id: int, name: str = None, expire_date=None, member_limit=None):
        """Create an invite link for the chat"""
        try:
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=chat_id,
                name=name,
                expire_date=expire_date,
                member_limit=member_limit
            )
            return invite_link.invite_link
        except TelegramError as e:
            logger.error(f"Failed to create invite link for {chat_id}: {e}")
            return None
