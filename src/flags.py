from discord.ext import commands
import datetime
import pytz
from utils.db import Database
import logging

logger = logging.getLogger(__name__)

class Flag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = Database()
        self.today = datetime.datetime.now(pytz.utc)

    async def sent_messages_after_joining(self, user_id, joined_at=None):
        # Check if the user has sent messages after joining
        if joined_at is None:
            with self.database.get_db_connection() as conn:
                result = conn.execute('''
                    SELECT MIN(created_at) as joined_at FROM messages
                    WHERE user_id = ?
                ''', (str(user_id),)).fetchone()
            joined_at = result['joined_at'] if result else self.today
        with self.database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) as message_count FROM messages
                WHERE user_id = ? AND created_at >= ?
            ''', (str(user_id), joined_at)).fetchone()
        return result['message_count'] > 0 if result else False

    async def messaged_within_x_days(self, user_id, days):
        # Check if the user has messaged within the specified number of days
        x_days_ago = self.today - datetime.timedelta(days=days)
        with self.database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) as message_count FROM messages
                WHERE user_id = ? AND created_at >= ?
            ''', (str(user_id), x_days_ago)).fetchone()
        return result['message_count'] > 0 if result else False

    async def above_x_messages(self, user_id, count):
        # Check if the user has sent more than the specified number of messages
        with self.database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) as message_count FROM messages
                WHERE user_id = ?
            ''', (str(user_id),)).fetchone()
        return result['message_count'] > count if result else False

    async def below_x_messages(self, user_id, count):
        # Check if the user has sent fewer than the specified number of messages
        with self.database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) as message_count FROM messages
                WHERE user_id = ?
            ''', (str(user_id),)).fetchone()
        return result['message_count'] < count if result else False

    async def never_messaged(self, user_id):
        # Check if the user has never sent a message
        with self.database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) as message_count FROM messages
                WHERE user_id = ?
            ''', (str(user_id),)).fetchone()
        return result['message_count'] == 0 if result else True

    async def no_role_assigned(self, user_id):
        # Check if the user has no role assigned
        # This method needs to be updated to fetch roles from the database or another source
        return False  # Placeholder implementation

    async def low_interaction_high_activity(self, user_id):
        # Check if the user has low interaction but high activity
        high_activity_threshold = 100
        low_interaction_threshold = 10
        with self.database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) as message_count FROM messages
                WHERE user_id = ?
            ''', (str(user_id),)).fetchone()
        message_count = result['message_count'] if result else 0
        return message_count > high_activity_threshold and message_count < low_interaction_threshold

    async def get_user_activity_flags(self, user_id, joined_at=None):
        # Combine all flags into one method
        flags = {
            "sent_messages_after_joining": await self.sent_messages_after_joining(user_id, joined_at),
            "messaged_within_30_days": await self.messaged_within_x_days(user_id, 30),
            "above_100_messages": await self.above_x_messages(user_id, 100),
            "below_10_messages": await self.below_x_messages(user_id, 10),
            "never_messaged": await self.never_messaged(user_id),
            "no_role_assigned": await self.no_role_assigned(user_id),
            "low_interaction_high_activity": await self.low_interaction_high_activity(user_id)
        }
        logger.info(f"Flags for user {user_id}: {flags}")
        return flags