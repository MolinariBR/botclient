#!/usr/bin/env python3
import sqlite3
import os
from pathlib import Path

def check_database():
    # Verificar se o banco existe no diretório atual
    db_path = Path('botclient.db')
    if db_path.exists():
        print(f'✅ Banco encontrado: {db_path.absolute()}')

        # Conectar e listar tabelas
        conn = sqlite3.connect('botclient.db')
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print('📋 Tabelas no banco:')
        for table in tables:
            print(f'  - {table[0]}')

        # Verificar se payments existe
        if ('payments',) in tables:
            print('✅ Tabela payments existe')

            # Verificar colunas da tabela payments
            cursor.execute('PRAGMA table_info(payments)')
            columns = cursor.fetchall()
            print('📋 Colunas da tabela payments:')
            for col in columns:
                print(f'  - {col[1]} ({col[2]})')
        else:
            print('❌ Tabela payments NÃO existe')

        conn.close()
    else:
        print('❌ Banco não encontrado')

if __name__ == "__main__":
    check_database()