import discord
from discord.ext import commands
import os
import logging
import datetime
import pytz
import sys
import asyncio  # For concurrent tasks
import sqlite3
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
    one_month_ago = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)
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
    try:
        async for message in channel.history(after=one_month_ago, limit=None):
            if not message.content:
                continue
            # Determine if message contains a link
            is_linked = 1 if 'http' in message.content else 0
            # Initial final_score set to 0; will be updated later
            final_score = 0
            messages_to_insert.append((
                str(message.author.id),
                message.author.name,
                str(channel.id),
                message.content,
                message.created_at,
                is_linked,
                final_score
            ))
        if messages_to_insert:
            # Perform a bulk insert to optimize DB writes
            with get_db_connection() as conn:
                conn.executemany('''
                    INSERT INTO messages (user_id, username, channel_id, content, created_at, is_linked, final_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', messages_to_insert)
                conn.commit()  # Ensure changes are saved
            logger.info(f'Inserted {len(messages_to_insert)} messages from channel: {channel.name}')
    except discord.Forbidden:
        logger.warning(f'Forbidden access to channel: {channel.name}')
    except Exception as e:
        logger.error(f'Error fetching messages from channel {channel.name}: {e}')

logger.info('Running bot')
bot.run(sensitive_vars.bot_token)  # Use bot token from sensitive variables
logger.info('Bot has stopped')
