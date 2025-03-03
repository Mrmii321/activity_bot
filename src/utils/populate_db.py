import discord
from discord.ext import commands
import os
import logging
import datetime
import pytz
import sys
import asyncio  # For concurrent tasks
import sqlite3
from datetime import timezone, datetime, timedelta  # Import timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Variables.sensitiveVars import SensitiveVariables
from utils.db import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize sensitive variables
sensitive_vars = SensitiveVariables()

intents = discord.Intents.all()
intents.message_content = True  # Enable the message content intent
bot = commands.Bot(command_prefix=',', intents=intents)

db = Database()

def get_db_connection():
    return db.get_db_connection()

@bot.event
async def on_ready():
    logger.info('Bot is ready')
    logger.info(f'Logged in as {bot.user}')
    await populate_db()
    logger.info('Database population complete')
    await bot.close()

async def populate_db():
    logger.info('Populating database with messages from the past month')
    one_month_ago = datetime.now(pytz.utc) - timedelta(days=30)  # Use timedelta correctly
    tasks = []
    # Create a task for each text channel in every guild
    for guild in bot.guilds:
        for channel in guild.text_channels:
            tasks.append(fetch_and_insert_channel_messages(channel, one_month_ago))
    await asyncio.gather(*tasks)
    logger.info('All channels processed.')

async def fetch_and_insert_channel_messages(channel, one_month_ago):
    logger.info(f'Fetching messages from channel: {channel.name}')
    messages_to_insert = []
    users_to_insert = []
    try:
        async for message in channel.history(after=one_month_ago, limit=None):
            if not message.content:
                continue
            # Determine if message contains a link
            is_linked = 1 if 'http' in message.content else 0
            # Compute the initial final_score
            final_score = compute_initial_score(message.author.id)
            messages_to_insert.append((
                str(message.author.id),
                message.author.name,
                str(channel.id),
                message.content,
                message.created_at,
                is_linked,
                final_score
             ))
            users_to_insert.append((
                str(message.author.id),
                message.author.name
            ))
        if messages_to_insert:
            # Perform a bulk insert to optimize DB writes
            with get_db_connection() as conn:
                conn.executemany('''
                    INSERT INTO messages (user_id, username, channel_id, content, created_at, is_linked, final_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', messages_to_insert)
                conn.executemany('''
                    INSERT OR IGNORE INTO users (id, username)
                    VALUES (?, ?)
                ''', users_to_insert)
                conn.commit()  # Ensure changes are saved
            logger.info(f'Inserted {len(messages_to_insert)} messages from channel: {channel.name}')
    except discord.Forbidden:
        logger.warning(f'Forbidden access to channel: {channel.name}')
    except Exception as e:
        logger.error(f'Error fetching messages from channel {channel.name}: {e}')

def compute_initial_score(user_id):
    """Compute the initial score for a user."""
    with get_db_connection() as conn:
        cur = conn.execute('''
            SELECT COUNT(*) as msg_count, MAX(created_at) as last_message
            FROM messages
            WHERE user_id = ? AND created_at >= datetime('now','-30 days')
        ''', (user_id,))
        result = cur.fetchone()
        msg_count = result['msg_count'] if result and result['msg_count'] is not None else 0
        last_message = result['last_message']
        if last_message:
            try:
                last_message_dt = datetime.fromisoformat(last_message)
            except Exception as e:
                logger.error(f"Error parsing last_message for user {user_id}: {e}")
                last_message_dt = datetime.now(timezone.utc)
            days_since = (datetime.now(timezone.utc) - last_message_dt).days
        else:
            days_since = 999  # High penalty if no messages

        # Build a row dictionary similar to what FlagScanner uses
        row = {
            'messages_past_month': msg_count,
            'days_since_last_message': days_since,
            'sent_messages_after_joining': False,
            'messaged_within_30_days': False,
            'above_100_messages': False,
            'below_10_messages': False,
            'never_messaged': False,
            'no_role_assigned': False,
            'low_interaction_high_activity': False
        }

        score = 0
        # Base score from messages
        for i in range(msg_count):
            score += 5 + (i * 0.2)

        # Incorporate flag contributions (flags default to False here)
        flag_weights = {
            "sent_messages_after_joining": 50,
            "messaged_within_30_days": 100,
            "above_100_messages": 150,
            "below_10_messages": -50,
            "never_messaged": -200,
            "no_role_assigned": -100,
            "low_interaction_high_activity": -150
        }
        for flag, weight in flag_weights.items():
            if row.get(flag):
                score += weight

        # Time adjustment based on recency
        if days_since <= 7:
            for _ in range(7 - days_since):
                score += 10
        elif days_since > 30:
            for _ in range(days_since - 30):
                score -= 5

        return score

logger.info('Running bot')
bot.run(sensitive_vars.bot_token)  # Use bot token from sensitive variables
logger.info('Bot has stopped')
