import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from utils.db import initialize_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file

intents = discord.Intents.all()
intents.message_content = True  # Enable the message content intent
bot = commands.Bot(command_prefix=',', intents=intents)

logger.info('Starting bot')

async def load_cogs():
    logger.info('Loading cogs')
    await bot.load_extension('cogs.flag_scanner')
    await bot.load_extension('cogs.inactive_users')
    logger.info('Cogs loaded')


@bot.event
async def on_ready():
    logger.info('Bot is ready')
    logger.info(f'Logged in as {bot.user}')
    await load_cogs()
    logger.info('All cogs are loaded and bot is ready to use')

initialize_db()  # Initialize the database
logger.info('Running bot')
bot.run(os.getenv('DISCORD_TOKEN'))  # Use environment variable for the token
logger.info('Bot has stopped')