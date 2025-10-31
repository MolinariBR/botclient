#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.utils.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.admin import Admin

print('Checking database...')
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    admins = db.query(Admin).all()
    print(f'Total admins: {len(admins)}')
    for admin in admins:
        print(f'ID: {admin.telegram_id}, Username: {admin.username}, Permissions: {admin.permissions}')
finally:
    db.close()