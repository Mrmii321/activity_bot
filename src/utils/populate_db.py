import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import datetime
import pytz
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file

intents = discord.Intents.all()
intents.message_content = True  # Enable the message content intent
bot = commands.Bot(command_prefix=',', intents=intents)

@bot.event
async def on_ready():
    logger.info('Bot is ready')
    logger.info(f'Logged in as {bot.user}')
    await populate_db()
    logger.info('Database population complete')
    await bot.close()

async def populate_db():
    logger.info('Populating database with messages from the past month')
    one_month_ago = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=30)
    for guild in bot.guilds:
        for channel in guild.text_channels:
            logger.info(f'Fetching messages from channel: {channel.name}')
            try:
                async for message in channel.history(after=one_month_ago, limit=None):
                    if not message.content:
                        continue
                    with get_db_connection() as conn:
                        conn.execute('''
                            INSERT INTO messages (user_id, channel_id, content, created_at)
                            VALUES (?, ?, ?, ?)
                        ''', (str(message.author.id), str(channel.id), message.content, message.created_at))
                        logger.info(f'Message added to database: {message.content}')
            except discord.Forbidden:
                logger.warning(f'Forbidden access to channel: {channel.name}')
                continue
    logger.info('Database population complete')

logger.info('Running bot')
bot.run(os.getenv('DISCORD_TOKEN'))  # Use environment variable for the token
logger.info('Bot has stopped')
