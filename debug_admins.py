#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.admin import Admin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_admins_handler():
    # Conectar ao banco
    engine = create_engine('sqlite:///botclient.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get all admins
        admins = session.query(Admin).all()
        logger.info(f'Found {len(admins)} admins in database')

        if not admins:
            print('👨‍💼 Nenhum administrador encontrado.')
            return

        # Format admin list
        admins_text = f"👨‍💼 **Administradores do Sistema ({len(admins)})**\n\n"

        for i, admin in enumerate(admins, 1):
            logger.info(f'Processing admin {i}: telegram_id={admin.telegram_id}, username={admin.username}')
            admin_id = admin.telegram_id
            username = admin.username or "N/A"
            first_name = admin.first_name or ""
            last_name = admin.last_name or ""
            full_name = f"{first_name} {last_name}".strip()
            if not full_name:
                full_name = "N/A"
            permissions = admin.permissions or "basic"
            created_at = admin.created_at.strftime("%Y-%m-%d") if admin.created_at else "N/A"

            admin_block = f"🆔 **ID:** {admin_id}\n"
            admin_block += f"👤 **Nome:** {full_name}\n"
            admin_block += f"📱 **Username:** @{username}\n"
            admin_block += f"🔐 **Permissões:** {permissions}\n"
            admin_block += f"📅 **Desde:** {created_at}\n\n"

            admins_text += admin_block
            logger.info(f"Added admin {i} to response text")

        # Check message length
        if len(admins_text) > 4000:
            logger.warning(f"Admin list message too long ({len(admins_text)} chars), truncating")
            admins_text = admins_text[:3950] + "\n\n... (mensagem truncada)"

        logger.info(f"Sending admin list with {len(admins)} admins")
        print("=== MENSAGEM QUE SERIA ENVIADA ===")
        print(admins_text)
        print(f"=== FIM DA MENSAGEM (comprimento: {len(admins_text)} caracteres) ===")

    except Exception as e:
        logger.error(f"Failed to get admins list: {e}")
        print(f"❌ Falha ao obter lista de administradores: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    test_admins_handler()