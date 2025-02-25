import discord
from discord.ext import commands
import aiohttp
import logging

logger = logging.getLogger(__name__)

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Updated endpoint to point to the Flask server running on port 8000
        self.endpoint = r'http://localhost:8000/leaderboard'

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.endpoint) as resp:
                    if resp.status == 200:
                        data = await resp.text()
                        await ctx.send(f'Leaderboard:\n{data}')
                    else:
                        await ctx.send('Could not fetch leaderboard data.')
            except Exception as e:
                logger.error(f'Error fetching leaderboard: {e}')
                await ctx.send('Error fetching leaderboard.')


def setup(bot):
    bot.add_cog(Leaderboard(bot))
