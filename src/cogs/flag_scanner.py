import pandas as pd
import datetime
import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

today = pd.Timestamp.now()

class FlagScanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.df = pd.DataFrame(columns=["user_id", "last_message", "messages_past_month", "warnings", "days_since_last_message", "final_score"])
        logger.info("FlagScanner cog initialized")

    async def _initialize_dataframe(self, guild):
        """Initialize the DataFrame with user data and calculate initial scores."""
        logger.info("Initializing DataFrame with user data")
        user_data = []
        for member in guild.members:
            logger.info(f"Fetching data for member: {member.id}")
            user_id = member.id
            last_message = await self._get_last_message_time(member)
            messages_past_month = await self._get_messages_past_month(member)
            warnings = await self._get_warnings(member)
            user_data.append({
                "user_id": user_id,
                "last_message": last_message,
                "messages_past_month": messages_past_month,
                "warnings": warnings
            })
        df = pd.DataFrame(user_data)
        df["last_message"] = pd.to_datetime(df["last_message"])
        df["days_since_last_message"] = (today - df["last_message"]).dt.days
        df["final_score"] = df.apply(self._calculate_score, axis=1)
        self.df = df
        logger.info("DataFrame initialization complete")

    async def _get_last_message_time(self, member):
        """Fetch the last message time for a member."""
        logger.info(f"Fetching last message time for member: {member.id}")
        last_message = None
        for channel in member.guild.text_channels:
            logger.info(f"Checking channel: {channel.name}")
            try:
                async for message in channel.history(limit=100):
                    if message.author == member:
                        logger.info(f"Found message from member: {message.created_at}")
                        if last_message is None or message.created_at > last_message:
                            last_message = message.created_at
            except discord.Forbidden:
                logger.warning(f"Forbidden access to channel: {channel.name}")
                continue
        logger.info(f"Last message time for member {member.id}: {last_message}")
        return last_message

    async def _get_messages_past_month(self, member):
        """Fetch the number of messages sent by a member in the past month."""
        logger.info(f"Fetching messages past month for member: {member.id}")
        count = 0
        one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        for channel in member.guild.text_channels:
            logger.info(f"Checking channel: {channel.name}")
            try:
                async for message in channel.history(after=one_month_ago, limit=100):
                    if message.author == member:
                        count += 1
                        logger.info(f"Message count for member {member.id}: {count}")
            except discord.Forbidden:
                logger.warning(f"Forbidden access to channel: {channel.name}")
                continue
        logger.info(f"Messages past month for member {member.id}: {count}")
        return count

    async def _get_warnings(self, member):
        """Fetch the number of warnings for a member."""
        logger.info(f"Fetching warnings for member: {member.id}")
        # Implement your logic to fetch warnings for the member
        warnings = 0  # Placeholder
        logger.info(f"Warnings for member {member.id}: {warnings}")
        return warnings

    def _calculate_score(self, row):
        """Calculate the score for a given user row."""
        logger.info(f"Calculating score for row: {row}")
        score = 100  # Start with max score
        
        # Deduct points for inactivity
        if row["days_since_last_message"] > 30:
            score -= 40
        elif row["days_since_last_message"] > 14:
            score -= 20
        elif row["days_since_last_message"] > 7:
            score -= 10
        
        # Add points for activity
        if row["messages_past_month"] > 100:
            score += 30
        elif row["messages_past_month"] > 50:
            score += 20
        elif row["messages_past_month"] > 20:
            score += 10
        
        # Deduct points for warnings
        score -= row["warnings"] * 10
        
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
    async def check_score(self, ctx, member: discord.Member):
        """Command to check the score of a mentioned user."""
        user_id = member.id
        logger.info(f"Checking score for user ID: {user_id}")
        await self._initialize_dataframe(ctx.guild)
        score = await self.calculate_score(user_id)
        await ctx.send(f"{member.mention}'s score is {score}")

async def setup(bot):
    await bot.add_cog(FlagScanner(bot))
    logger.info("FlagScanner cog added to bot")