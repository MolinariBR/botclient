import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import ContextTypes

from src.models.admin import Admin
from src.models.group import Group, GroupMembership
from src.models.payment import Payment
from src.models.user import User
from src.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class AdminHandlers:
    def __init__(self, db: Session, telegram_service: TelegramService):
        self.db = db
        self.telegram = telegram_service

    async def add_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat

        if not user or not message or not chat:
            return

        # Check if user is admin
        admin = self.db.query(Admin).filter_by(telegram_id=str(user.id)).first()
        if not admin:
            await message.reply_text("Acesso negado. Você não é um administrador.")
            return

        # FR-004: Restrict admin commands to private chat only
        if chat.type != "private":
            await message.reply_text("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")
            return

        # Parse username and group_id from args
        if not context.args or len(context.args) < 2:
            await message.reply_text("Uso: /add @username <group_telegram_id>")
            return

        username = context.args[0].lstrip("@")
        group_telegram_id = context.args[1]

        # Find user by username
        db_user = self.db.query(User).filter_by(username=username).first()
        if not db_user:
            await message.reply_text(f"Usuário @{username} não encontrado. Certifique-se de que o usuário iniciou uma conversa com o bot.")
            return

        # Find or create group
        group = self.db.query(Group).filter_by(telegram_group_id=group_telegram_id).first()
        if not group:
            group = Group(
                telegram_group_id=group_telegram_id,
                name=f"Grupo VIP {group_telegram_id}"
            )
            self.db.add(group)
            self.db.commit()

        # Check if already member
        membership = self.db.query(GroupMembership).filter_by(
            user_id=db_user.id, group_id=group.id
        ).first()
        if membership:
            await message.reply_text(f"Usuário @{username} já é membro deste grupo.")
            return

        # Add membership
        membership = GroupMembership(user_id=db_user.id, group_id=group.id)
        self.db.add(membership)
        self.db.commit()

        # Admit user to group (send invite link)
        invite_link = await self.telegram.create_chat_invite_link(
            int(group.telegram_group_id),
            name=f"Convite para {db_user.username}"
        )

        if invite_link:
            success = await self.telegram.send_message(
                int(db_user.telegram_id),
                f"Você foi adicionado ao grupo VIP: {group.name}\n\nLink de convite: {invite_link}"
            )
        else:
            success = await self.telegram.send_message(
                int(db_user.telegram_id),
                f"Você foi adicionado ao grupo VIP: {group.name}\n\nEntre em contato com o admin para acesso."
            )

        if success:
            await message.reply_text(f"Usuário @{username} adicionado com sucesso ao grupo.")
        else:
            await message.reply_text(f"Usuário @{username} adicionado ao banco de dados, mas falha ao notificar.")

    async def register_group_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register_group command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat

        if not user or not message or not chat:
            return

        # Check if user is admin
        admin = self.db.query(Admin).filter_by(telegram_id=str(user.id)).first()
        if not admin:
            await message.reply_text("Acesso negado. Você não é um administrador.")
            return

        # FR-004: Restrict admin commands to private chat only
        if chat.type != "private":
            await message.reply_text("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")
            return

        # Parse group_id from args
        if not context.args or len(context.args) < 1:
            await message.reply_text("Uso: /register_group <group_telegram_id>")
            return

        group_telegram_id = context.args[0]

        # Check if group already exists
        existing_group = self.db.query(Group).filter_by(telegram_group_id=group_telegram_id).first()
        if existing_group:
            await message.reply_text(f"Grupo {group_telegram_id} já está registrado.")
            return

        # Create group
        group = Group(
            telegram_group_id=group_telegram_id,
            name=f"Grupo VIP {group_telegram_id}"
        )
        self.db.add(group)
        self.db.commit()

        await message.reply_text(f"Grupo {group_telegram_id} registrado com sucesso.")

    async def group_id_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /group_id command - show current group ID"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat

        if not user or not message or not chat:
            return

        # Check if user is admin
        admin = self.db.query(Admin).filter_by(telegram_id=str(user.id)).first()
        if not admin:
            await message.reply_text("Acesso negado. Você não é um administrador.")
            return

        # This command can be used in groups to get the ID
        if chat.type == "private":
            await message.reply_text("Este comando deve ser usado em um grupo.")
            return

        await message.reply_text(f"ID do grupo: {chat.id}")

    async def kick_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /kick command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat

        if not user or not message or not chat:
            return

        # Check if user is admin
        admin = self.db.query(Admin).filter_by(telegram_id=str(user.id)).first()
        if not admin:
            await message.reply_text("Acesso negado. Você não é um administrador.")
            return

        # FR-004: Restrict admin commands to private chat only
        if chat.type != "private":
            await message.reply_text("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")
            return

        # Parse username from args
        if not context.args or len(context.args) < 1:
            await message.reply_text("Uso: /kick @username")
            return

        username = context.args[0].lstrip("@")

        # Find user by username
        db_user = self.db.query(User).filter_by(username=username).first()
        if not db_user:
            await message.reply_text(f"Usuário @{username} não encontrado.")
            return

        # Find group
        group = self.db.query(Group).filter_by(telegram_group_id=str(chat.id)).first()
        if not group:
            await message.reply_text("Este grupo não está registrado como grupo VIP.")
            return

        # Check if user is member of this group
        membership = self.db.query(GroupMembership).filter_by(
            user_id=db_user.id, group_id=group.id
        ).first()
        if not membership:
            await message.reply_text(f"Usuário @{username} não é membro deste grupo.")
            return

        # Remove membership from database
        self.db.delete(membership)
        self.db.commit()

        # Kick user from Telegram group
        kicked = await self.telegram.kick_chat_member(
            int(group.telegram_group_id), int(db_user.telegram_id)
        )

        if kicked:
            await message.reply_text(f"Usuário @{username} removido do grupo com sucesso.")
        else:
            await message.reply_text(f"Usuário @{username} removido do banco de dados, mas falha ao remover do grupo Telegram.")

    async def ban_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ban command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat

        if not user or not message or not chat:
            return

        # Check if user is admin
        admin = self.db.query(Admin).filter_by(telegram_id=str(user.id)).first()
        if not admin:
            await message.reply_text("Acesso negado. Você não é um administrador.")
            return

        # FR-004: Restrict admin commands to private chat only
        if chat.type != "private":
            await message.reply_text("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")
            return

        # Parse username from args
        if not context.args or len(context.args) < 1:
            await message.reply_text("Uso: /ban @username")
            return

        username = context.args[0].lstrip("@")

        # Find user by username
        db_user = self.db.query(User).filter_by(username=username).first()
        if not db_user:
            await message.reply_text(f"Usuário @{username} não encontrado.")
            return

        # Check if user is already banned
        if db_user.is_banned:
            await message.reply_text(f"Usuário @{username} já está banido.")
            return

        # Ban the user
        db_user.is_banned = True

        # Remove user from all groups
        memberships = self.db.query(GroupMembership).filter_by(user_id=db_user.id).all()
        for membership in memberships:
            self.db.delete(membership)

            # Try to kick from Telegram group
            try:
                # Get group info to kick user
                group = self.db.query(Group).filter_by(id=membership.group_id).first()
                if group:
                    await self.telegram.kick_chat_member(
                        int(group.telegram_group_id), int(db_user.telegram_id)
                    )
            except Exception as e:
                logger.warning(f"Failed to kick user {db_user.telegram_id} from group {membership.group_id}: {e}")

        # Commit changes
        self.db.commit()

        await message.reply_text(f"Usuário @{username} banido permanentemente.")

    async def broadcast_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /broadcast command - send message to all group members"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat

        if not user or not message or not chat:
            return

        # Check if user is admin
        admin = self.db.query(Admin).filter_by(telegram_id=str(user.id)).first()
        if not admin:
            await message.reply_text("Acesso negado. Você não é um administrador.")
            return

        # FR-004: Restrict admin commands to private chat only
        if chat.type != "private":
            await message.reply_text("❌ Comandos administrativos só podem ser executados no chat privado com o bot.")
            return

        # Parse message from args
        if not context.args or len(context.args) < 1:
            await message.reply_text("Uso: /broadcast <mensagem>")
            return

        broadcast_message = " ".join(context.args)

        # Send broadcast to all members
        await self._broadcast_to_all_members(broadcast_message)

        await message.reply_text("Mensagem enviada para todos os membros!")

    async def _broadcast_to_all_members(self, message: str):
        """Send message to all groups"""
        # Get all groups
        groups = self.db.query(Group).all()
        logger.info(f"Broadcasting to {len(groups)} groups: {[g.telegram_group_id for g in groups]}")

        for group in groups:
            try:
                logger.info(f"Sending broadcast to group {group.telegram_group_id}")
                # Send message to each group
                result = await self.telegram.send_message(
                    int(group.telegram_group_id),
                    f"📢 **Mensagem do Administrador**\n\n{message}"
                )
                logger.info(f"Broadcast sent successfully to group {group.telegram_group_id}")
            except Exception as e:
                logger.error(f"Failed to send broadcast to group {group.telegram_group_id}: {e}")
                # Continue with other groups even if one fails
