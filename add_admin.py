#!/usr/bin/env python3
"""
Script para adicionar administradores
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.admin import Admin
from utils.config import Config

def add_admin(telegram_id: str, username: str = None, first_name: str = None, permissions: str = "basic"):
    """Add admin to database"""
    engine = create_engine(Config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if admin already exists
        existing = db.query(Admin).filter_by(telegram_id=telegram_id).first()
        if existing:
            print(f"Admin {telegram_id} já existe!")
            return

        # Create new admin
        admin = Admin(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            permissions=permissions
        )
        db.add(admin)
        db.commit()
        print(f"Admin {telegram_id} adicionado com sucesso!")

    except Exception as e:
        db.rollback()
        print(f"Erro ao adicionar admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python add_admin.py <telegram_id> [username] [first_name] [permissions]")
        print("Exemplo: python add_admin.py 123456789 admin_user João basic")
        sys.exit(1)

    telegram_id = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else None
    first_name = sys.argv[3] if len(sys.argv) > 3 else None
    permissions = sys.argv[4] if len(sys.argv) > 4 else "basic"

    add_admin(telegram_id, username, first_name, permissions)