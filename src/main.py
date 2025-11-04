#!/usr/bin/env python3
# main.py - Versão refatorada (arquivo único, logs em nível INFO/ERROR)

import os
import sys
import asyncio
import logging
import traceback

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import telegram
import httpx

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
)

# Handlers / Services / Utils (assumo que já existem em seu projeto)
from handlers.admin_handlers import AdminHandlers
from handlers.user_handlers import UserHandlers
from utils.config import Config
from utils.logger import setup_logging
from services.mute_service import MuteService
from services.pixgo_service import PixGoService
from services.usdt_service import USDTService
from services.telegram_service import TelegramService
from services.logging_service import LoggingService

# ---------- CONFIG / ENV ----------
load_dotenv(".env.local")  # chamado apenas uma vez
# Carregar token a partir do Config para coerência
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or getattr(Config, "TELEGRAM_TOKEN", None)

# ---------- LOG (produção: INFO + ERROR) ----------
# Se utils.logger.setup_logging existe, preferi usá-lo; caso contrário, fallback.
try:
    log_level = getattr(Config, "LOG_LEVEL", "INFO")
    log_file = getattr(Config, "LOG_FILE", "logs/bot.log")
    setup_logging(log_level, log_file)
except Exception:
    # Fallback básico
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # reduzir ruído de libs

# ---------- DATABASE ----------
def init_database():
    if not getattr(Config, "DATABASE_URL", None):
        logging.error("DATABASE_URL não configurada em Config.")
        raise RuntimeError("DATABASE_URL não configurada")
    engine = create_engine(Config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

# ---------- SERVICES ----------
def init_services(db_session):
    """
    Inicializa e retorna as instâncias de serviço necessárias.
    db_session pode ser None se o serviço não precisar dele.
    """
    pixgo = PixGoService(Config.PIXGO_API_KEY, Config.PIXGO_BASE_URL)
    usdt = USDTService(Config.USDT_WALLET_ADDRESS)
    telegram_svc = TelegramService(Config.TELEGRAM_TOKEN)
    mute = MuteService(db_session)
    logging_svc = LoggingService()
    logging.info("Serviços inicializados.")
    return {
        "pixgo": pixgo,
        "usdt": usdt,
        "telegram": telegram_svc,
        "mute": mute,
        "logging": logging_svc,
    }

# ---------- HANDLERS SETUP ----------
def setup_handlers(application: Application, user_handlers: UserHandlers, admin_handlers: AdminHandlers, mute_service: MuteService):
    """
    Registra todos os handlers no Application.
    Handlers utilitários (message_logger/chat_member_handler) definidos apenas aqui.
    """
    logging.info("🔧 Registrando handlers...")

    async def message_logger(update, context):
        try:
            message = getattr(update, "message", None)
            if message:
                user = update.effective_user
                chat = update.effective_chat
                text = message.text or "[non-text]"
                logging.info(f"MESSAGE: '{text}' from {user.username or user.first_name} in {chat.type} ({chat.id})")
        except Exception as e:
            logging.error(f"Erro em message_logger: {e}")

    async def chat_member_handler(update, context):
        try:
            chat_member = getattr(update, "chat_member", None)
            if chat_member:
                chat = chat_member.chat
                new = chat_member.new_chat_member
                status = new.status
                me = await context.bot.get_me()
                if new.user and new.user.id == me.id:
                    logging.info(f"Bot status in {chat.title or chat.id}: {status}")
                    if status == "member":
                        await context.bot.send_message(chat_id=chat.id, text="🤖 Bot adicionado ao grupo. Use /help.")
        except Exception as e:
            logging.error(f"Erro em chat_member_handler: {e}")

    # Registrar handlers (ordem e grupos pensados para evitar conflito)
    application.add_handler(MessageHandler(filters.ALL, message_logger), group=1)
    application.add_handler(ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER), group=1)

    # User commands
    application.add_handler(CommandHandler("start", user_handlers.start_handler))
    application.add_handler(CommandHandler("help", user_handlers.help_handler))
    application.add_handler(CommandHandler("status", user_handlers.status_handler))
    application.add_handler(CommandHandler("pay", user_handlers.pay_handler))
    application.add_handler(CommandHandler("renew", user_handlers.renew_handler))
    application.add_handler(CommandHandler("cancel", user_handlers.cancel_handler))
    application.add_handler(CommandHandler("support", user_handlers.support_handler))
    application.add_handler(CommandHandler("info", user_handlers.info_handler))
    application.add_handler(CommandHandler("invite", user_handlers.invite_handler))

    # Admin commands
    admin_cmds = [
        ("add", admin_handlers.add_handler),
        ("addadmin", admin_handlers.addadmin_handler),
        ("kick", admin_handlers.kick_handler),
        ("ban", admin_handlers.ban_handler),
        ("unban", admin_handlers.unban_handler),
        ("mute", admin_handlers.mute_handler),
        ("unmute", admin_handlers.unmute_handler),
        ("warn", admin_handlers.warn_handler),
        ("resetwarn", admin_handlers.resetwarn_handler),
        ("expire", admin_handlers.expire_handler),
        ("sendto", admin_handlers.sendto_handler),
        ("userinfo", admin_handlers.userinfo_handler),
        ("pending", admin_handlers.pending_handler),
        ("confirm", admin_handlers.confirm_payment_handler),
        ("reject", admin_handlers.reject_payment_handler),
        ("setprice", admin_handlers.setprice_handler),
        ("settime", admin_handlers.settime_handler),
        ("setwallet", admin_handlers.setwallet_handler),
        ("rules", admin_handlers.rules_handler),
        ("welcome", admin_handlers.welcome_handler),
        ("schedule", admin_handlers.schedule_handler),
        ("stats", admin_handlers.stats_handler),
        ("logs", admin_handlers.logs_handler),
        ("admins", admin_handlers.admins_handler),
        ("settings", admin_handlers.settings_handler),
        ("backup", admin_handlers.backup_handler),
        ("restore", admin_handlers.restore_handler),
        ("restore_quick", admin_handlers.restore_handler),
        ("broadcast", admin_handlers.broadcast_handler),
        ("register_group", admin_handlers.register_group_handler),
        ("group_id", admin_handlers.group_id_handler),
    ]
    for cmd, handler in admin_cmds:
        application.add_handler(CommandHandler(cmd, handler))

    # Handlers de debug/test (não respondem em produção por padrão)
    async def group_message_test(update, context):
        try:
            message = update.message
            if message and message.chat and message.chat.type in ("group", "supergroup"):
                if message.text and message.text.upper().startswith("TEST:"):
                    await message.reply_text(f"Grupo detectado! ID: {message.chat.id}")
        except Exception as e:
            logging.error(f"Erro group_message_test: {e}")

    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, group_message_test), group=-5)

    # Handler for USDT payment proofs (photos in private chats)
    application.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, user_handlers.proof_handler))

    logging.info("Handlers registrados com sucesso.")

# ---------- RUNNER (polling / webhook robusto) ----------
async def run_polling_loop(application: Application):
    """
    Loop de polling robusto com tratamento de erros e backoff.
    Garante que webhook seja deletado e aplica reconexões com backoff.
    """
    max_retries = 5
    retry_delay = 5.0

    for attempt in range(max_retries):
        try:
            logging.info(f"Inicializando bot (tentativa {attempt + 1}/{max_retries})")
            # Test connectivity
            try:
                me = await application.bot.get_me()
                logging.info(f"Conectado ao Telegram: @{me.username} (id={me.id})")
            except Exception as conn_err:
                logging.error(f"Não foi possível conectar ao Telegram: {conn_err}")
                raise

            await application.initialize()
            # Escolha webhook vs polling
            webhook_url = os.getenv("WEBHOOK_URL")
            port = os.getenv("PORT")
            use_webhook = bool(webhook_url and port and os.getenv("ENVIRONMENT") == "production")

            if use_webhook:
                try:
                    await application.bot.set_webhook(url=webhook_url, allowed_updates=["message", "callback_query", "chat_member"])
                    logging.info("Webhook configurado com sucesso.")
                    # Em webhook, normalmente o servidor HTTP cuidará das atualizações
                    # Aqui assumimos que infra web está disponível
                except Exception as wh_err:
                    logging.warning(f"Falha ao configurar webhook: {wh_err}. CAINDO para polling.")
                    use_webhook = False

            if not use_webhook:
                # Polling mode
                try:
                    await application.bot.delete_webhook(drop_pending_updates=True)
                except Exception:
                    logging.debug("Nenhum webhook para deletar ou falha ao deletar.")

                logging.info("Bot iniciado com polling manual.")

                consecutive_errors = 0
                max_consecutive = 10
                base_delay = 1.0
                max_delay = 60.0
                poll_cycle = 0
                last_update_id = 0  # Para controlar o offset das mensagens

                while True:
                    poll_cycle += 1
                    try:
                        async with asyncio.timeout(30):
                            updates = await application.bot.get_updates(
                                offset=last_update_id + 1,
                                timeout=25,
                                allowed_updates=["message", "callback_query", "chat_member"]
                            )
                        if updates:
                            for update in updates:
                                try:
                                    await application.process_update(update)
                                    last_update_id = max(last_update_id, update.update_id)
                                except Exception as e:
                                    logging.error(f"Erro ao processar update {getattr(update, 'update_id', '?')}: {e}")
                            consecutive_errors = 0
                        await asyncio.sleep(0.1)
                    except asyncio.TimeoutError:
                        consecutive_errors = 0
                        await asyncio.sleep(0.1)
                    except (telegram.error.NetworkError, httpx.ReadError, httpx.ConnectError) as net_err:
                        consecutive_errors += 1
                        delay = min(base_delay * (2 ** consecutive_errors), max_delay)
                        logging.warning(f"Erro de rede (#{consecutive_errors}): {net_err}. Retry em {delay:.1f}s")
                        if consecutive_errors >= max_consecutive:
                            logging.error("Muitos erros consecutivos de rede. Reiniciando processo de inicialização.")
                            raise net_err
                        await asyncio.sleep(delay)
                    except Exception as e:
                        logging.error(f"Erro inesperado no loop de polling: {e}")
                        await asyncio.sleep(1)

        except Exception as e:
            logging.error(f"Erro na execução do bot (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                logging.info(f"Retry em {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 1.5
            else:
                logging.error("Máximo de tentativas atingido. Abortando.")
                raise

# ---------- ASYNC MAIN (inicia serviços concorrentes) ----------
async def main_async(application: Application, mute_service: MuteService):
    # Start mute/background services
    try:
        await mute_service.start()
    except Exception as e:
        logging.error(f"Falha ao iniciar mute service: {e}")

    try:
        await run_polling_loop(application)
    except KeyboardInterrupt:
        logging.info("Sinal de interrupção recebido.")
    finally:
        try:
            await mute_service.stop()
            logging.info("Mute service finalizado.")
        except Exception as e:
            logging.error(f"Erro ao parar mute service: {e}")

# ---------- ENTRYPOINT MAIN ----------
def main():
    try:
        # Valida token
        if not TELEGRAM_TOKEN:
            logging.error("TELEGRAM_TOKEN não encontrado. Abortando.")
            raise SystemExit("TELEGRAM_TOKEN não encontrado")

        # Valida Config (se existir um método validate, usa)
        try:
            errors = Config.validate() if hasattr(Config, "validate") else None
            if errors:
                logging.error("Erros de configuração detectados:")
                for err in errors:
                    logging.error(f" - {err}")
                raise SystemExit("Configuração inválida")
        except Exception as e:
            # Se validate não existir, apenas logamos e continuamos
            logging.debug(f"Validação Config pulada/erro: {e}")

        # Inicializa DB e Services
        engine, SessionLocal = init_database()
        db = SessionLocal()
        services = init_services(db)

        # Inicializa Handlers
        user_handlers = UserHandlers(db, services["pixgo"], services["usdt"])
        admin_handlers = AdminHandlers(db, services["telegram"], services["logging"])

        # Cria Application
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()

        # Registra handlers
        setup_handlers(application, user_handlers, admin_handlers, services["mute"])

        # Executa loop principal (bloqueante)
        asyncio.run(main_async(application, services["mute"]))

    except Exception as e:
        logging.error(f"CRITICAL ERROR no main(): {e}")
        logging.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
