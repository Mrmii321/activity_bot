import discord
import datetime
import pytz
import os
import sys
from utils.db import Database

class UserActivity:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    async def get_inactive_users(self):
        all_members = self.bot.get_all_members()
        active_user_ids = set()
        with self.db.get_db_connection() as conn:
            result = conn.execute('''
                SELECT user_id FROM messages WHERE is_linked = 1
            ''').fetchall()
            for row in result:
                active_user_ids.add(row['user_id'])
        inactive_users = [member.name for member in all_members if str(member.id) not in active_user_ids]
        return inactive_users

    async def get_active_user_count(self):
        active_user_ids = set()
        with self.db.get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(DISTINCT user_id) as active_user_count FROM messages
            ''').fetchone()
            active_user_count = result['active_user_count']
        print(f"Active users count: {active_user_count}")
        return active_user_count

