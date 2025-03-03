from threading import Thread
import webapp
import discord
from discord.ext import commands
import logging
from utils.db import Database
from Variables.sensitiveVars import SensitiveVariables
from cogs.flag_scanner import FlagScanner
from cogs.leaderboard import Leaderboard
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize sensitive variables
sensitive_vars = SensitiveVariables()

# Initialize the database
Database().initialize_db()

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix=',', intents=intents)

logger.info('Starting bot')

async def load_cogs():
    await bot.add_cog(FlagScanner(bot))
    await bot.add_cog(Leaderboard(bot))

@bot.event
async def on_ready():
    await load_cogs()
    logger.info('Bot is ready')

# Start the Flask web server in a separate thread
logger.info('Starting Flask web server on port 8000')
flask_thread = Thread(target=webapp.app.run, kwargs={'port':8000, 'debug': False, 'use_reloader': False})
flask_thread.start()

logger.info('Running bot')
bot.run(sensitive_vars.bot_token)
logger.info('Bot has stopped')
def stop_flask_thread():
    logger.info('Stopping Flask web server')
    flask_thread.join()

atexit.register(stop_flask_thread)