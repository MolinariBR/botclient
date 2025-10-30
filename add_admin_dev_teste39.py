import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.admin import Admin
from src.utils.config import Config

def add_admin(telegram_id, username, first_name=None, permissions="basic"):
    engine = create_engine(Config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Admin).filter_by(telegram_id=telegram_id).first()
        if existing:
            print(f"Admin {telegram_id} já existe!")
            return
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
    # Substitua pelo seu telegram_id real
    telegram_id = input("Digite o telegram_id do admin: ")
    username = "dev_teste39"
    first_name = None
    add_admin(telegram_id, username, first_name)
