import discord
from discord.ext import commands
import logging
from utils.db import Database
from Variables.sensitiveVars import SensitiveVariables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize sensitive variables
sensitive_vars = SensitiveVariables()

# Initialize the database
database = Database()

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

database.initialize_db()  # Initialize the database
logger.info('Running bot')
bot.run(sensitive_vars.bot_token)  # Use bot token from sensitive variables
logger.info('Bot has stopped')