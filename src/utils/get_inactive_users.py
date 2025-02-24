import discord
import datetime
import pytz
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db import get_db_connection


async def get_inactive_users(bot):
    all_members = bot.get_all_members()
    active_user_ids = set()
    with get_db_connection() as conn:
        result = conn.execute('''
            SELECT user_id FROM messages
        ''').fetchall()
        for row in result:
            active_user_ids.add(row['user_id'])
    inactive_users = [member.name for member in all_members if str(member.id) not in active_user_ids]
    return inactive_users

async def get_active_user_count(bot):
    active_user_ids = set()
    with get_db_connection() as conn:
        result = conn.execute('''
            SELECT COUNT(DISTINCT user_id) as active_user_count FROM messages
        ''').fetchone()
        active_user_count = result['active_user_count']
    print(f"Active users count: {active_user_count}")
    return active_user_count

