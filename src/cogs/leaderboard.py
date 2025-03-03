import discord
from discord.ext import commands
import aiohttp
import logging
import pandas as pd  # Added import for pandas

logger = logging.getLogger(__name__)

# New function to provide leaderboard data for the webapp

def get_leaderboard():
    data = {
        "username": ["User1", "User2", "User3"],
        "score": [100, 200, 150]
    }
    return pd.DataFrame(data)


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Updated endpoint to point to the Flask server running on port 8000
        self.endpoint = r'http://localhost:8000/leaderboard'

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx, limit: int = 10):
        """Get the leaderboard of top users."""
        async with aiohttp.ClientSession() as session:
            try:
                params = {'limit': limit}
                async with session.get(self.endpoint, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.text()
                        await ctx.send(f'Leaderboard:\n```{data}```')
                    else:
                        await ctx.send('Could not fetch leaderboard data.')
            except Exception as e:
                logger.error(f'Error fetching leaderboard: {e}')
                await ctx.send('Error fetching leaderboard.')


def setup(bot):
    bot.add_cog(Leaderboard(bot))
