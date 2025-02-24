import sqlite3
from contextlib import closing
import logging
import os

class Database:
    DATABASE_PATH = 'src/data/messages.db'

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_db_connection(self):
        conn = sqlite3.connect(self.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_db(self):
        if not os.path.exists(os.path.dirname(self.DATABASE_PATH)):
            os.makedirs(os.path.dirname(self.DATABASE_PATH))

        self.logger.info('Initializing database')
        with closing(self.get_db_connection()) as conn:
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

                # Check for missing columns and add them
                existing_columns = {row['name'] for row in conn.execute("PRAGMA table_info(messages)")}
                required_columns = {
                    'id', 'user_id', 'channel_id', 'content', 'created_at', 'is_linked'
                }

                missing_columns = required_columns - existing_columns
                for column in missing_columns:
                    if column == 'is_linked':
                        conn.execute('ALTER TABLE messages ADD COLUMN is_linked BOOLEAN DEFAULT 0')
                    # Add other columns if needed with appropriate default values or constraints

        self.logger.info('Database initialized')
