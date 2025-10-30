import datetime
import logging

from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.models.payment import Payment
from src.models.user import User
from src.services.pixgo_service import PixGoService
from src.services.usdt_service import USDTService
from src.utils.config import Config
from src.utils.performance import measure_performance, measure_block

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

        if chat.type == "private":
            # Welcome message for private chats
            private_welcome = f"""
👋 Olá {user.first_name}!

🤖 **Bot VIP Telegram**

Este bot gerencia acesso a grupos VIP através de assinaturas.

💰 **Preço:** R$ {Config.SUBSCRIPTION_PRICE}
⏰ **Duração:** {Config.SUBSCRIPTION_DAYS} dias

📱 **Como usar:**
1. Adicione o bot a um grupo
2. Use `/addadmin @seu_username` para se tornar admin
3. Use `/help` no grupo para ver comandos

❓ **Suporte:** Use /help para mais informações
"""
            logger.info(f"✅ Sending private welcome to {user.first_name}")
            await message.reply_text(private_welcome, parse_mode="Markdown")
            return

        # Group welcome message
        welcome_text = f"""
👋 Olá {user.first_name}!

Bem-vindo ao Bot VIP Telegram! 🚀

Este bot permite que você tenha acesso a grupos VIP exclusivos através de assinatura.

💰 **Preço:** R$ {Config.SUBSCRIPTION_PRICE}
⏰ **Duração:** {Config.SUBSCRIPTION_DAYS} dias

Use /help para ver todos os comandos disponíveis.
"""
        logger.info(f"✅ Sending group welcome to {user.first_name}")
        await message.reply_text(welcome_text, parse_mode="Markdown")

    @measure_performance("user_handlers.pay_handler")
    async def pay_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pay command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # User commands should work in groups only
        if chat.type == "private":
            await message.reply_text("❌ Comandos de usuário só podem ser executados em grupos.")
            return

        # Check if user already has active subscription
        db_user = self.db.query(User).filter_by(telegram_id=str(user.id)).first()
        if db_user and db_user.status_assinatura == "active":
            await message.reply_text("Você já possui uma assinatura ativa!")
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
        """Handle /status command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # User commands should work in groups only
        if chat.type == "private":
            await message.reply_text("❌ Comandos de usuário só podem ser executados em grupos.")
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
        """Handle /renew command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # User commands should work in groups only
        if chat.type == "private":
            await message.reply_text("❌ Comandos de usuário só podem ser executados em grupos.")
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
            qr_code = self.pixgo.get_qr_code(pix_payment["id"])
            payment = Payment(
                user_id=db_user.id,
                pixgo_payment_id=pix_payment["id"],
                amount=Config.SUBSCRIPTION_PRICE,
                payment_method="pix",
            )
            self.db.add(payment)
            self.db.commit()

            payment_message = f"""
🔄 **Renovação de Assinatura**

Valor: R$ {Config.SUBSCRIPTION_PRICE:.2f}
Descrição: Renovação de Assinatura VIP

{qr_code}

Após o pagamento, sua assinatura será estendida automaticamente por mais {Config.SUBSCRIPTION_DAYS} dias.
"""
            await message.reply_text(payment_message, parse_mode="Markdown")
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

        user = query.from_user
        if not user:
            return

        # Get user from database
        db_user = self.db.query(User).filter_by(telegram_id=str(user.id)).first()
        if not db_user:
            await query.answer("Usuário não encontrado. Tente novamente.")
            return

        payment_method = query.data

        if payment_method == "pay_pix":
            # Create PIX payment
            pix_payment = self.pixgo.create_payment(
                amount=Config.SUBSCRIPTION_PRICE,
                description=f"Assinatura VIP - {user.username or user.first_name}",
                payer_info={"telegram_id": str(user.id)},
            )

            if pix_payment:
                payment = Payment(
                    user_id=db_user.id,
                    pixgo_payment_id=pix_payment["payment_id"],
                    amount=Config.SUBSCRIPTION_PRICE,
                    payment_method="pix",
                )
                self.db.add(payment)
                self.db.commit()

                # Send QR code image
                await query.message.reply_photo(
                    photo=pix_payment["qr_image_url"],
                    caption=f"""🎯 **Pagamento PIX**

Valor: R$ {Config.SUBSCRIPTION_PRICE:.2f}
Descrição: Assinatura VIP

**Código PIX:**
```
{pix_payment["qr_code"]}
```

Após o pagamento, aguarde a confirmação automática.""",
                    parse_mode="Markdown"
                )
                await query.answer("Pagamento PIX gerado com sucesso!")
            else:
                await query.message.reply_text("❌ Erro ao gerar pagamento PIX. Tente novamente.")
                await query.answer("Erro no pagamento PIX")

        elif payment_method == "pay_usdt":
            # Create USDT payment
            usdt_instructions = self.usdt.get_payment_instructions(
                Config.SUBSCRIPTION_PRICE
            )

            payment = Payment(
                user_id=db_user.id,
                amount=Config.SUBSCRIPTION_PRICE,
                payment_method="usdt",
            )
            self.db.add(payment)
            self.db.commit()

            await query.message.reply_text(
                f"""₿ **Pagamento USDT (Polygon)**

Valor: R$ {Config.SUBSCRIPTION_PRICE:.2f} ≈ ${Config.SUBSCRIPTION_PRICE * 0.2:.2f} USDT
Descrição: Assinatura VIP

{usdt_instructions}

Após o pagamento, aguarde a confirmação automática.""",
                parse_mode="Markdown"
            )
            await query.answer("Instruções USDT enviadas!")

        # Edit the original message to remove buttons
        await query.message.edit_text(
            f"""✅ **Método selecionado: {'PIX' if payment_method == 'pay_pix' else 'USDT'}**

Valor: R$ {Config.SUBSCRIPTION_PRICE:.2f}
Descrição: Assinatura VIP

Aguarde as instruções de pagamento...""",
            parse_mode="Markdown"
        )

    @measure_performance("user_handlers.help_handler")
    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command - show available commands"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # Check if user is admin
        from src.models.admin import Admin
        is_admin = self.db.query(Admin).filter(Admin.telegram_id == user.id).first() is not None

        help_text = f"""
🤖 **Bot VIP Telegram - Ajuda**

Olá {user.first_name}! Aqui estão os comandos disponíveis:

---

## � **Comandos de Usuário**

`/start` — Inicia o bot e mostra informações básicas
`/help` — Mostra esta mensagem de ajuda
`/pay` — Gera QR Code ou link de pagamento para assinatura
`/status` — Verifica o status da sua assinatura
`/renew` — Renova sua assinatura automaticamente
`/cancel` — Cancela a renovação automática da assinatura
`/support` — Abre canal de suporte com administradores
`/info` — Mostra informações sobre o grupo/mentoria
`/invite` — Gera seu link pessoal de convite

---

## 👑 **Comandos Administrativos**
"""

        if is_admin:
            help_text += """
### Gerenciamento de Membros
`/add @usuario` — Adiciona manualmente um usuário
`/kick @usuario` — Remove um usuário do grupo
`/ban @usuario` — Bane permanentemente um usuário
`/unban @usuario` — Remove o banimento de um usuário
`/mute @usuario [tempo]` — Silencia um usuário por tempo determinado
`/unmute @usuario` — Remove o silêncio de um usuário
`/warn @usuario [motivo]` — Envia um aviso ao usuário
`/resetwarn @usuario` — Zera os avisos do usuário
`/userinfo @usuario` — Exibe informações detalhadas do usuário

### Controle de Acesso & Assinaturas
`/check @usuario` — Verifica status do pagamento/assinatura
`/renew @usuario` — Renova manualmente a assinatura do usuário
`/expire @usuario` — Expira manualmente o acesso do usuário
`/pending` — Lista usuários com pagamentos pendentes

### Comunicação & Anúncios
`/broadcast [mensagem]` — Envia mensagem para todos os membros
`/schedule [hora] [mensagem]` — Programa mensagem automática
`/rules` — Envia as regras do grupo
`/welcome` — Define mensagem de boas-vindas
`/sendto @usuario [mensagem]` — Envia mensagem privada

### Configurações & Monitoramento
`/settings` — Abre painel de configurações do bot
`/admins` — Lista todos os administradores
`/stats` — Mostra estatísticas do grupo
`/logs` — Exibe últimas ações do bot
`/backup` — Exporta dados do grupo
`/restore` — Importa backup anterior

### Configuração do Sistema
`/setprice [valor] [moeda]` — Define preço da assinatura
`/settime [dias]` — Define duração do acesso
`/setwallet [endereço]` — Define carteira para pagamentos
`/register_group` — Registra o grupo atual
`/group_id` — Mostra ID do grupo atual

---
"""
        else:
            help_text += """
*Comandos administrativos disponíveis apenas para admins.*
"""

        help_text += """
� **Dicas:**
• Use comandos apenas em grupos (exceto /start em privado)
• Mencione usuários com @ para comandos que requerem alvo
• Alguns comandos podem ter parâmetros opcionais entre []

📞 **Suporte:** Use /support para falar com administradores
"""

    @measure_performance("user_handlers.cancel_handler")
    async def cancel_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command - disable auto-renewal"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # User commands should work in groups only
        if chat.type == "private":
            await message.reply_text("❌ Comandos de usuário só podem ser executados em grupos.")
            return

        # Find user in database
        db_user = self.db.query(User).filter_by(telegram_id=str(user.id)).first()
        if not db_user:
            await message.reply_text("❌ Usuário não encontrado. Use /start primeiro.")
            return

        # Check if user has active subscription
        if db_user.status_assinatura != "active":
            await message.reply_text("❌ Você não possui uma assinatura ativa para cancelar.")
            return

        # Disable auto-renewal
        db_user.auto_renew = False
        self.db.commit()

        await message.reply_text(
            "✅ **Renovação automática desabilitada com sucesso!**\n\n"
            "Sua assinatura atual permanecerá ativa até a data de expiração.\n"
            "Para reativar a renovação automática, entre em contato com o suporte."
        )

    @measure_performance("user_handlers.support_handler")
    async def support_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command - provide support contact information"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # User commands should work in groups only
        if chat.type == "private":
            await message.reply_text("❌ Comandos de usuário só podem ser executados em grupos.")
            return

        support_text = """
🆘 **Suporte Técnico**

Para obter ajuda, entre em contato conosco:

📧 **Email:** suporte@viptelegram.com
💬 **Telegram:** @suporte_vip_bot
📱 **WhatsApp:** +55 11 99999-9999

⏰ **Horário de atendimento:**
Segunda a Sexta: 9h às 18h
Sábado: 9h às 12h

📋 **Antes de contactar, verifique:**
• Status da sua assinatura com /status
• Histórico de pagamentos com /payment_history
• Grupos disponíveis com /groups

Para questões urgentes, use o Telegram @suporte_vip_bot
"""
        await message.reply_text(support_text, parse_mode="Markdown")

    @measure_performance("user_handlers.info_handler")
    async def info_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command - show VIP group/mentorship information"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # User commands should work in groups only
        if chat.type == "private":
            await message.reply_text("❌ Comandos de usuário só podem ser executados em grupos.")
            return

        info_text = """
ℹ️ **Sobre o Grupo VIP Telegram**

🎯 **O que oferecemos:**
• Acesso exclusivo a grupos VIP do Telegram
• Conteúdo premium e atualizações diárias
• Suporte prioritário 24/7
• Comunidade ativa de profissionais

💰 **Planos e Preços:**
• **Básico:** R$ {Config.SUBSCRIPTION_PRICE:.2f} por {Config.SUBSCRIPTION_DAYS} dias
• **Renovação automática:** Disponível (pode ser desabilitada com /cancel)

📊 **Estatísticas:**
• +1000 membros ativos
• 15+ grupos especializados
• Atualização diária de conteúdo

🚀 **Como participar:**
1. Use /pay para fazer o pagamento
2. Aguarde a confirmação do pagamento
3. Use /join para entrar nos grupos disponíveis

📞 **Dúvidas?** Use /support para falar conosco

🌟 **Junte-se à nossa comunidade VIP hoje mesmo!**
"""
        await message.reply_text(info_text, parse_mode="Markdown")

    async def invite_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /invite command"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # User commands should work in groups only
        if chat.type == "private":
            await message.reply_text("❌ Comandos de usuário só podem ser executados em grupos.")
            return

        # Check if user has active subscription
        db_user = self.db.query(User).filter_by(telegram_id=str(user.id)).first()
        if not db_user:
            await message.reply_text("Usuário não encontrado. Use /pay para assinar primeiro.")
            return

        # Check subscription status
        status = str(db_user.status_assinatura)
        if status != "ativo":
            await message.reply_text("Você precisa ter uma assinatura ativa para gerar links de convite.")
            return

        # Generate unique invite code (simple implementation)
        import uuid
        invite_code = str(uuid.uuid4())[:8]  # Short unique code

        # Derive bot username from token (basic implementation)
        bot_username = Config.TELEGRAM_TOKEN.split(':')[0] if Config.TELEGRAM_TOKEN else "bot"

        # For now, create a simple invite link format
        # In a full implementation, this would create a real Telegram invite link
        invite_link = f"https://t.me/{bot_username}?start=invite_{invite_code}"

        invite_text = f"""
🎫 **Link de Convite**

Seu link de convite exclusivo:
{invite_link}

Este link permite que novos usuários se juntem ao grupo VIP.
*Rastreamento será implementado em breve.*
"""
        await message.reply_text(invite_text, parse_mode="Markdown")

    @measure_performance("user_handlers.help_handler")
    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command - show available commands"""
        user = update.effective_user
        message = update.message
        chat = update.effective_chat
        if not user or not message or not chat:
            return

        # Check if user is admin
        from src.models.admin import Admin
        is_admin = self.db.query(Admin).filter(Admin.telegram_id == user.id).first() is not None

        # Determine help content based on chat type
        if chat.type == "private":
            # In private chat with bot: show ALL commands (admin interface)
            help_text = f"""
🤖 **Bot VIP Telegram - Painel Administrativo**

Olá {user.first_name}! Como administrador, você tem acesso a todos os comandos:

---

## 👤 **Comandos de Usuário**

`/start` — Inicia o bot e mostra informações básicas
`/help` — Mostra esta mensagem de ajuda
`/pay` — Gera QR Code ou link de pagamento para assinatura
`/status` — Verifica o status da sua assinatura
`/renew` — Renova sua assinatura automaticamente
`/cancel` — Cancela a renovação automática da assinatura
`/support` — Abre canal de suporte com administradores
`/info` — Mostra informações sobre o grupo/mentoria
`/invite` — Gera seu link pessoal de convite

---

## 👑 **Comandos Administrativos**
"""
            # Always show admin commands in private chat
            help_text += """
### Gerenciamento de Membros
`/add @usuario` — Adiciona manualmente um usuário
`/addadmin @usuario` — Adiciona um novo administrador
`/kick @usuario` — Remove um usuário do grupo
`/ban @usuario` — Bane permanentemente um usuário
`/unban @usuario` — Remove o banimento de um usuário
`/mute @usuario [tempo]` — Silencia um usuário por tempo determinado
`/unmute @usuario` — Remove o silêncio de um usuário
`/warn @usuario [motivo]` — Envia um aviso ao usuário
`/resetwarn @usuario` — Zera os avisos do usuário
`/userinfo @usuario` — Exibe informações detalhadas do usuário

### Controle de Acesso & Assinaturas
`/check @usuario` — Verifica status do pagamento/assinatura
`/renew @usuario` — Renova manualmente a assinatura do usuário
`/expire @usuario` — Expira manualmente o acesso do usuário
`/pending` — Lista usuários com pagamentos pendentes

### Comunicação & Anúncios
`/broadcast [mensagem]` — Envia mensagem para todos os membros
`/schedule [hora] [mensagem]` — Programa mensagem automática
`/rules` — Envia as regras do grupo
`/welcome` — Define mensagem de boas-vindas
`/sendto @usuario [mensagem]` — Envia mensagem privada

### Configurações & Monitoramento
`/settings` — Abre painel de configurações do bot
`/admins` — Lista todos os administradores
`/stats` — Mostra estatísticas do grupo
`/logs` — Exibe últimas ações do bot
`/backup` — Exporta dados do grupo
`/restore` — Importa backup anterior

### Configuração do Sistema
`/setprice [valor] [moeda]` — Define preço da assinatura
`/settime [dias]` — Define duração do acesso
`/setwallet [endereço]` — Define carteira para pagamentos
`/register_group` — Registra o grupo atual
`/group_id` — Mostra ID do grupo atual

---
"""
        else:
            # In group: show only user commands
            help_text = f"""
🤖 **Bot VIP Telegram - Ajuda**

Olá {user.first_name}! Aqui estão os comandos disponíveis para usuários:

---

## 👤 **Comandos de Usuário**

`/start` — Inicia o bot e mostra informações básicas
`/help` — Mostra esta mensagem de ajuda
`/pay` — Gera QR Code ou link de pagamento para assinatura
`/status` — Verifica o status da sua assinatura
`/renew` — Renova sua assinatura automaticamente
`/cancel` — Cancela a renovação automática da assinatura
`/support` — Abre canal de suporte com administradores
`/info` — Mostra informações sobre o grupo/mentoria
`/invite` — Gera seu link pessoal de convite

---

*Para comandos administrativos, use o chat privado com o bot.*
"""

        if chat.type == "private":
            # Admin tips in private chat
            help_text += """
💡 **Dicas Administrativas:**
• Use este chat privado para todos os comandos administrativos
• Mencione usuários com @ para comandos que requerem alvo
• Alguns comandos podem ter parâmetros opcionais entre []
• Use /register_group em um grupo para registrá-lo
• Use /group_id para obter o ID de qualquer grupo

📞 **Suporte:** Você é o administrador - gerencie tudo aqui!
"""
        else:
            # User tips in group
            help_text += """
💡 **Dicas:**
• Use comandos apenas em grupos
• Para comandos administrativos, fale comigo em privado
• Mencione usuários com @ para comandos que requerem alvo
• Alguns comandos podem ter parâmetros opcionais entre []

📞 **Suporte:** Use /support para falar com administradores
"""

        await message.reply_text(help_text, parse_mode="Markdown")
