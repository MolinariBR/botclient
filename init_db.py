#!/usr/bin/env python3
"""
Script para inicializar o banco de dados
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from models.base import Base
from models.user import User
from models.payment import Payment
from models.group import Group
from models.admin import Admin
from utils.config import Config

def init_db():
    """Initialize database tables"""
    engine = create_engine(Config.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()