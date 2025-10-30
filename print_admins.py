import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.admin import Admin
from src.utils.config import Config

def print_all_admins():
    engine = create_engine(Config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        admins = db.query(Admin).all()
        if not admins:
            print("Nenhum admin encontrado no banco de dados.")
        for admin in admins:
            print(f"telegram_id: {admin.telegram_id} | username: {admin.username} | first_name: {admin.first_name}")
    finally:
        db.close()

if __name__ == "__main__":
    print_all_admins()
