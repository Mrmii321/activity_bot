import pandas as pd
import datetime
import discord
from discord.ext import commands
import logging
import pytz
from utils.db import get_db_connection

import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

today = pd.Timestamp.now(tz=pytz.utc)

def dataframe_to_image(df, filename="table.png"):
    fig, ax = plt.subplots(figsize=(len(df.columns) * 1.5, len(df) * 0.5))
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.auto_set_column_width(col=list(range(len(df.columns))))  # Adjust column width
    plt.savefig(filename, bbox_inches='tight')
    plt.close()

class FlagScanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.df = pd.DataFrame(columns=["user_id", "last_message", "messages_past_month", "days_since_last_message", "final_score"])
        logger.info("FlagScanner cog initialized")
        self.member = None

    async def _initialize_dataframe(self, guild):
        """Initialize the DataFrame with user data and calculate initial scores."""
        logger.info("Initializing DataFrame with user data")
        user_data = []
        logger.info(f"Fetching data for member: {self.member.id}")
        user_id = self.member.id
        last_message = await self._get_last_message_time(self.member)
        messages_past_month = await self._get_messages_past_month(self.member)
        user_data.append({
            "user_id": user_id,
            "last_message": last_message,
            "messages_past_month": messages_past_month
        })
        df = pd.DataFrame(user_data)
        df["last_message"] = pd.to_datetime(df["last_message"])
        df["last_message"] = df["last_message"].dt.tz_localize('UTC', ambiguous='NaT') if df["last_message"].dt.tz is None else df["last_message"]
        df["days_since_last_message"] = (today - df["last_message"]).dt.days
        df["final_score"] = df.apply(self._calculate_score, axis=1)
        self.df = df
        logger.info("DataFrame initialization complete")

    async def _get_last_message_time(self, member):
        """Fetch the last message time for a member from the database."""
        logger.info(f"Fetching last message time for member: {member.id}")
        with get_db_connection() as conn:
            result = conn.execute('''
                SELECT created_at FROM messages
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (str(member.id),)).fetchone()
        last_message = result['created_at'] if result else None
        logger.info(f"Last message time for member {member.id}: {last_message}")
        return last_message

    async def _get_messages_past_month(self, member):
        """Fetch the number of messages sent by a member in the past month from the database."""
        logger.info(f"Fetching messages past month for member: {member.id}")
        one_month_ago = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=30)
        with get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) as message_count FROM messages
                WHERE user_id = ? AND created_at >= ?
            ''', (str(member.id), one_month_ago)).fetchone()
        count = result['message_count'] if result else 0
        logger.info(f"Messages past month for member {member.id}: {count}")
        return count

    def _calculate_score(self, row):
        """Calculate the score for a given user row."""
        logger.info(f"Calculating score for row: {row}")
        score = 100  # Start with max score
        
        # Deduct points for inactivity
        if row["days_since_last_message"] > 30:
            score -= min((row["days_since_last_message"] // 5) * 5, 50)
        elif row["days_since_last_message"] == None or 'NaT':
            score -= 50
        
        # Add points for activity (bonus starts at 100 and scales in 100‑point increments per 20 messages, capped at 1000)
        if row["messages_past_month"] > 20:
            score += min((row["messages_past_month"] // 20) * 100, 1000)

        
        logger.info(f"Final score for row: {score}")
        return max(score, 0)  # Ensure score doesn't go negative

    async def get_user_data(self, user_id):
        """Retrieve user data for a given user ID."""
        logger.info(f"Retrieving data for user ID: {user_id}")
        user_row = self.df[self.df["user_id"] == user_id]
        if not user_row.empty:
            logger.info(f"User data found for user ID: {user_id}")
            return user_row.iloc[0]
        logger.info(f"No user data found for user ID: {user_id}")
        return None

    async def calculate_score(self, user_id):
        """Calculate the score for a given user ID."""
        logger.info(f"Calculating score for user ID: {user_id}")
        user_data = await self.get_user_data(user_id)
        if user_data is not None:
            logger.info(f"User data found for user ID: {user_id}")
            return user_data["final_score"]
        logger.info(f"No user data found for user ID: {user_id}")
        return 0

    @commands.command(name="checkscore")
    async def check_score(self, ctx, member: discord.Member = None, user_id: int = None):
        """Command to check the score of a mentioned user or by user ID."""
        if member is None and user_id is None:
            await ctx.send("Please provide a user mention or user ID.")
            return
        
        if member is not None:
            user_id = member.id
        else:
            member = ctx.guild.get_member(user_id)
            if member is None:
                await ctx.send("User not found.")
                return
        
        start_time = datetime.datetime.now()
        self.member = member
        
        logger.info(f"Checking score for user ID: {user_id}")
        
        await self._initialize_dataframe(ctx.guild)
        score = await self.calculate_score(user_id)

        dataframe_to_image(self.df, "table.png")

        await ctx.send(f"{member.name}'s score is {score}", file=discord.File("table.png"))
        
        end_time = datetime.datetime.now()
        logger.info(f"Score check completed in {end_time - start_time}")

async def setup(bot):
    await bot.add_cog(FlagScanner(bot))
    logger.info("FlagScanner cog added to bot")