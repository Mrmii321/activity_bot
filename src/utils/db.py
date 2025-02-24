import sqlite3
from contextlib import closing
import logging
import os

DATABASE_PATH = 'src/data/messages.db'

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    if not os.path.exists(os.path.dirname(DATABASE_PATH)):
        os.makedirs(os.path.dirname(DATABASE_PATH))
        
    logger.info('Initializing database')
    with closing(get_db_connection()) as conn:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    is_linked BOOLEAN DEFAULT 0
                )
            ''')
    logger.info('Database initialized')
