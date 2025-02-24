import discord
from discord.ext import commands
from utils.get_inactive_users import UserActivity


class InactiveUsers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_activity = UserActivity(bot=bot)

    @commands.command(name='inactive_users')
    async def fetch_inactive_users(self, ctx):
        inactive_users = await self.user_activity.get_inactive_users()
        active_users = await self.user_activity.get_active_user_count()
        if not inactive_users:
            await ctx.send('No inactive users found.')
        else:
            user_list = ', '.join([str(user) for user in inactive_users])
            await ctx.send(f'Number of inactive users: {len(inactive_users)}')
            await ctx.send(f'active users: {active_users}')

async def setup(bot):
    await bot.add_cog(InactiveUsers(bot))
