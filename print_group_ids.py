import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.group import Group
from src.utils.config import Config

def print_all_group_ids():
    engine = create_engine(Config.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        groups = db.query(Group).all()
        if not groups:
            print("Nenhum grupo encontrado no banco de dados.")
        for group in groups:
            print(f"Nome: {group.name} | telegram_group_id: {group.telegram_group_id}")
    finally:
        db.close()

if __name__ == "__main__":
    print_all_group_ids()
