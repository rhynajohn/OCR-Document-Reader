import os

#database.py

import asyncpg

DATABASE_URL = "postgresql://postgres:12345@localhost/ocr_db"

connection_params = {
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', '12345'),
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'ocr_db'),
}

async def create_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

async def check_connection():
    try:
        pool = await create_db_pool()
        async with pool.acquire() as conn:
            await conn.execute('SELECT 1')
        return True
    except Exception as e:
        return False
