import datetime
import logging

from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from models.payment import Payment
from models.user import User
from services.pixgo_service import PixGoService
from services.usdt_service import USDTService
from utils.config import Config
from utils.performance import measure_performance, measure_block

logger = logging.getLogger(__name__)


class UserHandlers:
    def __init__(
        self,
        db_session: Session,
        pixgo_service: PixGoService,
        usdt_service: USDTService,
    ):
        self.db = db_session
        self.pixgo = pixgo_service
        self.usdt = usdt_service

    @measure_performance("user_handlers.start_handler")
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            logger.error("❌ Missing user, message or chat in start_handler")
            return

        logger.info(f"🚀 START COMMAND: from {user.username or user.first_name} in {chat.type} chat {chat.id}")

        # Unified welcome message for both private and group chats
        welcome_text = f"""
👋 Olá {user.first_name}!

🤖 **Bot VIP Telegram**

Este bot gerencia acesso a grupos VIP através de assinaturas automáticas.

💰 **Preço:** R$ {Config.SUBSCRIPTION_PRICE}
⏰ **Duração:** {Config.SUBSCRIPTION_DAYS} dias

📱 **Como usar:**
• Use `/pay` para gerar pagamento da assinatura
• Use `/status` para verificar sua assinatura
• Use `/help` para ver todos os comandos disponíveis

❓ **Suporte:** Use /support para falar com administradores
"""

        logger.info(f"✅ Sending unified welcome to {user.first_name}")
        await message.reply_text(welcome_text, parse_mode="Markdown")

    @measure_performance("user_handlers.pay_handler")
    async def pay_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pay command - works in both private and group chats"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # Check if user already has active subscription
        db_user = self.db.query(User).filter_by(telegram_id=str(user.id)).first()
        if db_user and db_user.status_assinatura == "active":
            await message.reply_text("✅ Você já possui uma assinatura ativa!")
            return

        # Create user if doesn't exist
        if not db_user:
            db_user = User(
                telegram_id=str(user.id),
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            self.db.add(db_user)
            self.db.commit()

        # Create payment method selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("💰 PIX (R$)", callback_data="pay_pix"),
                InlineKeyboardButton("₿ USDT (Polygon)", callback_data="pay_usdt"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await message.reply_text(
            f"""🎯 **Escolha o método de pagamento**

Valor: R$ {Config.SUBSCRIPTION_PRICE:.2f}
Descrição: Assinatura VIP (30 dias)

Selecione uma das opções abaixo:""",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    @measure_performance("user_handlers.status_handler")
    async def status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - works in both private and group chats"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        db_user = self.db.query(User).filter_by(telegram_id=str(user.id)).first()
        if not db_user:
            await message.reply_text("Usuário não encontrado. Certifique-se de ter iniciado uma conversa com o bot.")
            return

        # Format expiration date
        expiration_str = "N/A"
        if db_user.data_expiracao:
            if isinstance(db_user.data_expiracao, str):
                expiration_str = db_user.data_expiracao
            elif hasattr(db_user.data_expiracao, 'strftime'):
                expiration_str = db_user.data_expiracao.strftime("%d/%m/%Y")
            else:
                expiration_str = str(db_user.data_expiracao)

        # Format status - title case for English "active", leave others as-is
        status_display = db_user.status_assinatura.title() if db_user.status_assinatura.lower() == "active" else db_user.status_assinatura

        status_text = f"""
📊 **Status da Assinatura**

Status: {status_display}
Expiração: {expiration_str}
"""
        await message.reply_text(status_text, parse_mode="Markdown")

    @measure_performance("user_handlers.renew_handler")
    async def renew_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /renew command - works in both private and group chats"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # Check if user exists and has active subscription
        db_user = self.db.query(User).filter_by(telegram_id=str(user.id)).first()
        if not db_user:
            await message.reply_text("Usuário não encontrado. Use /pay para assinar primeiro.")
            return

        if db_user.status_assinatura != "active":
            await message.reply_text("Você não possui uma assinatura ativa. Use /pay para assinar.")
            return

        # Check if subscription is still valid (not expired)
        if db_user.data_expiracao and db_user.data_expiracao < datetime.datetime.utcnow():
            await message.reply_text("Sua assinatura expirou. Use /pay para renovar.")
            return

        # Create renewal payment
        pix_payment = self.pixgo.create_payment(
            amount=Config.SUBSCRIPTION_PRICE,
            description=f"Renovação de Assinatura VIP - {user.username or user.first_name}",
            payer_info={"telegram_id": str(user.id)},
        )

        if pix_payment:
            qr_code = pix_payment.get("qr_code")
            if not qr_code:
                await message.reply_text("❌ Erro ao gerar QR Code. Tente novamente.")
                return
                
            payment = Payment(
                user_id=db_user.id,
                pixgo_payment_id=pix_payment.get("payment_id", pix_payment.get("id", "unknown")),
                amount=Config.SUBSCRIPTION_PRICE,
                payment_method="pix",
            )
            self.db.add(payment)
            self.db.commit()

            qr_image_url = pix_payment.get('qr_image_url')
            
            if qr_image_url:
                # Send QR code as image with caption
                await message.reply_photo(
                    photo=qr_image_url,
                    caption=f"""🔄 **Renovação de Assinatura**

� **Valor:** R$ {Config.SUBSCRIPTION_PRICE:.2f}
📝 **Descrição:** Renovação de Assinatura VIP

⚠️ **Após o pagamento, sua assinatura será estendida automaticamente por mais {Config.SUBSCRIPTION_DAYS} dias.**"""
                )
            else:
                # Fallback to text-only version
                payment_message = f"""
�🔄 **Renovação de Assinatura**

Valor: R$ {Config.SUBSCRIPTION_PRICE:.2f}
Descrição: Renovação de Assinatura VIP

```
{qr_code}
```

Após o pagamento, sua assinatura será estendida automaticamente por mais {Config.SUBSCRIPTION_DAYS} dias.
"""
                await message.reply_text(payment_message)
        else:
            # Fallback to USDT
            usdt_instructions = self.usdt.get_payment_instructions(
                Config.SUBSCRIPTION_PRICE
            )
            await message.reply_text(
                f"PIX indisponível. Use USDT:\n{usdt_instructions}"
            )

    @measure_performance("user_handlers.payment_callback_handler")
    async def payment_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment method selection callbacks"""
        query = update.callback_query
        if not query:
            return

        await query.answer()

        user = update.effective_user
        chat = update.effective_chat
        callback_data = query.data

        if not user or not chat:
            return

        # Get or create user
        db_user = self.db.query(User).filter_by(telegram_id=str(user.id)).first()
        if not db_user:
            db_user = User(
                telegram_id=str(user.id),
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            self.db.add(db_user)
            self.db.commit()

        if callback_data == "pay_pix":
            await self._process_pix_payment(query, db_user, user)
        elif callback_data == "pay_usdt":
            await self._process_usdt_payment(query, db_user, user)
        else:
            await query.edit_message_text("❌ Método de pagamento inválido.")

    async def _process_pix_payment(self, query, db_user, user):
        """Process PIX payment"""
        try:
            # Create PIX payment
            pix_payment = self.pixgo.create_payment(
                amount=Config.SUBSCRIPTION_PRICE,
                description=f"Assinatura VIP - {user.first_name}",
                payer_info={"telegram_id": str(user.id)},
            )

            if not pix_payment:
                await query.edit_message_text("❌ Erro ao criar pagamento PIX. Tente novamente.")
                return

            # Get QR code
            payment_id = pix_payment.get("payment_id", pix_payment.get("id", "unknown"))
            qr_code = pix_payment.get("qr_code")
            if not qr_code:
                await query.edit_message_text("❌ Erro ao gerar QR Code. Tente novamente.")
                return

            # Save payment to database
            payment = Payment(
                user_id=db_user.id,
                amount=Config.SUBSCRIPTION_PRICE,
                payment_method="pix",
                pixgo_payment_id=payment_id,
                status="pending",
            )
            self.db.add(payment)
            self.db.commit()

            # Send payment details
            qr_image_url = pix_payment.get('qr_image_url')
            
            if qr_image_url:
                # First: Send info message
                info_text = f"""💰 **PAGAMENTO PIX GERADO**

👤 **Cliente:** {user.first_name}
💵 **Valor:** R$ {Config.SUBSCRIPTION_PRICE:.2f}
⏰ **Vencimento:** {pix_payment.get('expires_at', 'N/A')}"""
                
                await query.message.reply_text(info_text, parse_mode="Markdown")
                
                # Second: Send QR code as photo
                await query.message.reply_photo(
                    photo=qr_image_url,
                    caption="📱 QR Code PIX - Escaneie para pagar"
                )
                
                # Third: Send copyable code WITHOUT Markdown to avoid parsing errors
                qr_code = pix_payment.get("qr_code")
                
                code_text = f"""🔗 COPIE O CÓDIGO PIX:

{qr_code}

⚠️ Após o pagamento, envie o comprovante usando /proof"""
                
                await query.message.reply_text(code_text)
                
                # Update original message
                await query.edit_message_text(
                    "✅ Informações de pagamento enviadas!",
                    reply_markup=None
                )
            else:
                # Fallback to text-only version - WITHOUT Markdown to avoid parsing errors
                qr_code = pix_payment.get("qr_code")
                
                info_text = f"""💰 PAGAMENTO PIX GERADO

👤 Cliente: {user.first_name}
💵 Valor: R$ {Config.SUBSCRIPTION_PRICE:.2f}
⏰ Vencimento: {pix_payment.get('expires_at', 'N/A')}"""

                await query.message.reply_text(info_text)
                
                code_text = f"""🔗 COPIE O CÓDIGO PIX:

{qr_code}

⚠️ Após o pagamento, envie o comprovante usando /proof"""
                
                await query.message.reply_text(code_text)
                
                await query.edit_message_text(
                    "✅ Informações de pagamento enviadas!"
                )

        except Exception as e:
            logger.error(f"Erro ao processar pagamento PIX: {e}")
            await query.edit_message_text("❌ Erro interno. Tente novamente.")

    async def _process_usdt_payment(self, query, db_user, user):
        """Process USDT payment"""
        try:
            # Create USDT payment record
            payment = Payment(
                user_id=db_user.id,
                amount=Config.SUBSCRIPTION_PRICE,
                payment_method="usdt",
                status="waiting_proof",
            )
            self.db.add(payment)
            self.db.commit()

            # Send USDT payment instructions
            usdt_text = f"""
₿ **PAGAMENTO USDT (POLYGON)**

👤 **Cliente:** {user.first_name}
💵 **Valor:** R$ {Config.SUBSCRIPTION_PRICE:.2f}
💎 **Valor em USDT:** ≈{(Config.SUBSCRIPTION_PRICE / 300):.4f} USDT

🏦 **Carteira Polygon:**
```
{Config.USDT_WALLET_ADDRESS}
```

📋 **Instruções:**
1. Envie exatamente **{(Config.SUBSCRIPTION_PRICE / 300):.4f} USDT** para o endereço acima
2. Use a rede **Polygon** (não Ethereum mainnet)
3. Tire uma foto/print do comprovante de transação
4. Envie a imagem usando o comando **/proof** neste grupo

⚠️ **IMPORTANTE:**
- Envie apenas para a rede **Polygon**
- Valor exato para evitar perdas
- Comprovante obrigatório para ativação
"""

            await query.edit_message_text(
                usdt_text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Erro ao processar pagamento USDT: {e}")
            import time
            await query.edit_message_text(f"❌ Erro interno. Tente novamente. ({int(time.time())})")

    @measure_performance("user_handlers.help_handler")
    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # Check if user is admin
        from models.admin import Admin
        is_admin = self.db.query(Admin).filter(Admin.telegram_id == str(user.id)).first() is not None

        if is_admin:
            # Admin help
            help_text = """
🤖 **BOT VIP TELEGRAM - PAINEL ADMIN**

👑 **Comandos de Administração:**

👥 **Gerenciamento de Membros:**
• `/add @usuario` - Adicionar membro
• `/kick @usuario` - Expulsar membro
• `/ban @usuario` - Banir membro
• `/unban @usuario` - Desbanir membro
• `/mute @usuario [tempo]` - Silenciar membro
• `/unmute @usuario` - Dessilenciar membro

⚠️ **Sistema de Avisos:**
• `/warn @usuario [motivo]` - Dar aviso
• `/resetwarn @usuario` - Resetar avisos

💰 **Pagamentos:**
• `/pending` - Ver pagamentos pendentes
• `/confirm ID` - Confirmar pagamento
• `/reject ID` - Rejeitar pagamento

⚙️ **Configurações:**
• `/setprice valor` - Alterar preço
• `/settime dias` - Alterar duração
• `/setwallet endereco` - Alterar carteira USDT

📊 **Estatísticas:**
• `/stats` - Ver estatísticas
• `/logs` - Ver logs recentes

📋 **Outros:**
• `/rules` - Ver regras
• `/welcome` - Configurar boas-vindas
• `/schedule` - Agendar mensagens
• `/backup` - Fazer backup
• `/restore` - Restaurar backup
"""
        else:
            # User help
            help_text = f"""
🤖 **BOT VIP TELEGRAM**

💰 **Preço:** R$ {Config.SUBSCRIPTION_PRICE}
⏰ **Duração:** {Config.SUBSCRIPTION_DAYS} dias

📋 **Comandos Disponíveis:**

🚀 **Básicos:**
• `/start` - Iniciar bot
• `/help` - Esta mensagem
• `/status` - Ver seu status
• `/info` - Informações do grupo

💳 **Pagamentos:**
• `/pay` - Gerar pagamento da assinatura
• `/renew` - Renovar assinatura
• `/cancel` - Cancelar assinatura

🆘 **Suporte:**
• `/support` - Contatar suporte
• `/invite` - Gerar link de convite

📸 **Comprovantes:**
• `/proof` - Enviar comprovante (após pagar)

⚠️ **IMPORTANTE:**
• Use `/pay` para assinar ou renovar
• Envie comprovantes de pagamento após realizar a transação
• Contate suporte em caso de dúvidas
"""

        await message.reply_text(help_text, parse_mode="Markdown")

    @measure_performance("user_handlers.proof_handler")
    async def proof_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo proofs sent in private chats"""
        user = update.effective_user
        message = update.message
        if not user or not message:
            return

        # Only process in private chats
        if update.effective_chat.type != "private":
            return

        # Check if message has photo
        if not message.photo:
            await message.reply_text("❌ Envie uma foto do comprovante de pagamento.")
            return

        # Get the largest photo
        photo = message.photo[-1]

        try:
            # Download photo
            file = await context.bot.get_file(photo.file_id)
            photo_url = file.file_path

            # Check for pending USDT payment
            pending_payment = self.db.query(Payment).filter_by(
                user_id=self.db.query(User).filter_by(telegram_id=str(user.id)).first().id,
                status="waiting_proof"
            ).first()

            if not pending_payment:
                await message.reply_text("❌ Nenhum pagamento pendente encontrado. Use /pay primeiro.")
                return

            # Update payment with proof
            from datetime import datetime
            pending_payment.proof_image_url = photo_url
            pending_payment.status = "waiting_proof"
            pending_payment.proof_submitted_at = datetime.now()
            self.db.commit()

            # Notify user
            await message.reply_text(
                "✅ **Comprovante recebido!**\n\n"
                "Seu comprovante foi enviado para análise dos administradores.\n"
                "Você será notificado quando for aprovado.",
                parse_mode="Markdown"
            )

            # Notify admins about new proof
            await self._notify_admins_new_proof(pending_payment, user, context)

        except Exception as e:
            logger.error(f"Erro ao processar comprovante: {e}")
            await message.reply_text("❌ Erro ao processar comprovante. Tente novamente.")

    async def _notify_admins_new_proof(self, payment: Payment, user, context=None):
        """Notify all admins about new USDT payment proof"""
        from models.admin import Admin

        admins = self.db.query(Admin).all()

        notification_text = f"""
🔔 **Novo comprovante USDT recebido!**

👤 **Usuário:** {user.first_name} (@{user.username or 'sem username'})
💰 **Valor:** R$ {payment.amount:.2f}
🆔 **ID do Pagamento:** {payment.id}

📸 **Comprovante:** [Ver imagem]({payment.proof_image_url})

Use /pending para ver todos os pagamentos pendentes.
"""

        for admin in admins:
            try:
                if context and hasattr(context, 'bot'):
                    await context.bot.send_message(
                        chat_id=admin.telegram_id,
                        text=notification_text,
                        parse_mode="Markdown"
                    )
                else:
                    logger.error("Context not available for admin notification")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin.telegram_id}: {e}")

    @measure_performance("user_handlers.cancel_handler")
    async def cancel_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        await message.reply_text("Função de cancelamento em desenvolvimento.")

    @measure_performance("user_handlers.support_handler")
    async def support_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        await message.reply_text("Para suporte, contate os administradores do grupo.")

    @measure_performance("user_handlers.info_handler")
    async def info_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        info_text = f"""
📊 **INFORMAÇÕES DO GRUPO**

🏷️ **Nome:** {chat.title or 'N/A'}
🆔 **ID:** {chat.id}
👥 **Tipo:** {chat.type}
📅 **Criado em:** {chat.date if hasattr(chat, 'date') else 'N/A'}

💰 **Preço da Assinatura:** R$ {Config.SUBSCRIPTION_PRICE}
⏰ **Duração:** {Config.SUBSCRIPTION_DAYS} dias
"""

        await message.reply_text(info_text, parse_mode="Markdown")

    @measure_performance("user_handlers.invite_handler")
    async def invite_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /invite command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        try:
            invite_link = await context.bot.create_chat_invite_link(chat.id)
            await message.reply_text(f"🔗 Link de convite: {invite_link.invite_link}")
        except Exception as e:
            logger.error(f"Erro ao criar link de convite: {e}")
            await message.reply_text("❌ Erro ao gerar link de convite.")
