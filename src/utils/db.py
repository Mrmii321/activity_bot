import os
import sqlite3
import logging
from contextlib import closing

class Database:
    def __init__(self, db_path='src/data/messages.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Create messages table with username column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                is_linked BOOLEAN DEFAULT 0,
                final_score INTEGER DEFAULT 0
            )
        ''')
        # Create roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                user_id TEXT NOT NULL,
                role_id TEXT NOT NULL,
                PRIMARY KEY (user_id, role_id)
            )
        ''')
        # Create flags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flags (
                user_id INTEGER,
                flag TEXT
            )
        ''')
        # Create scores table for potential future use
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                user_id INTEGER,
                score INTEGER DEFAULT 0
            )
        ''')
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def initialize_db(self):
        # Called at startup to ensure tables are created
        self.create_tables()

    def add_flag(self, user_id, flag):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO flags (user_id, flag) VALUES (?, ?)', (user_id, flag))
        self.conn.commit()

    def get_flags_by_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT flag FROM flags WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    def update_final_score(self, user_id, score):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE messages SET final_score = ? WHERE user_id = ?', (score, str(user_id)))
        self.conn.commit()

    def get_db_connection(self):
        """Return a new database connection with row factory set."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
