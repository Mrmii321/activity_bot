import pandas as pd
import datetime
import discord
from discord.ext import commands
import logging
import pytz
from utils.db import Database
from flags import Flag

import matplotlib.pyplot as plt
import seaborn as sns
import re
from utils.score_calculator import calculate_score  # added import for shared score calculation

database = Database()
database.initialize_db()

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
        self.flag = Flag(bot)
        self.db = Database()

    async def _initialize_dataframe(self):
        """Initialize the DataFrame with user data and calculate initial scores from the database."""
        logger.info("Initializing DataFrame with user data from the database")
        user_data = []
        with database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT DISTINCT user_id FROM messages
            ''').fetchall()
        
        for row in result:
            user_id = row['user_id']
            logger.info(f"Fetching data for user: {user_id}")
            last_message = await self._get_last_message_time(user_id)
            messages_past_month = await self._get_messages_past_month(user_id)
            flags = await self.flag.get_user_activity_flags(user_id)
            user_data.append({
                "user_id": user_id,
                "last_message": last_message,
                "messages_past_month": messages_past_month,
                **flags
            })
        
        df = pd.DataFrame(user_data)
        df["last_message"] = pd.to_datetime(df["last_message"])
        df["last_message"] = df["last_message"].dt.tz_localize('UTC', ambiguous='NaT') if df["last_message"].dt.tz is None else df["last_message"]
        df["days_since_last_message"] = (today - df["last_message"]).dt.days
        logger.info(f"Calculating score for user {row['user_id']}")
        df["final_score"] = df.apply(self._calculate_score, axis=1)
        logger.info(f"Calculated scores: {df[['user_id', 'final_score']]}")
        self.df = df
        logger.info("DataFrame initialization complete")
        logger.info(f"DataFrame content: {self.df}")

        # Update the final scores in the database
        for _, row in df.iterrows():
            logger.info(f"Updating final score for user {row['user_id']} to {row['final_score']}")
            database.update_final_score(row['user_id'], row['final_score'])

    async def _get_last_message_time(self, user_id):
        """Fetch the last message time for a user from the database."""
        logger.info(f"Fetching last message time for user: {user_id}")
        with database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT created_at FROM messages
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (str(user_id),)).fetchone()
        last_message = result['created_at'] if result else None
        logger.info(f"Last message time for user {user_id}: {last_message}")
        return last_message

    async def _get_messages_past_month(self, user_id):
        """Fetch the number of messages sent by a user in the past month from the database."""
        logger.info(f"Fetching messages past month for user: {user_id}")
        one_month_ago = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=30)
        with database.get_db_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) as message_count FROM messages
                WHERE user_id = ? AND created_at >= ?
            ''', (str(user_id), one_month_ago)).fetchone()
        count = result['message_count'] if result else 0
        logger.info(f"Messages past month for user {user_id}: {count}")
        return count

    def _calculate_score(self, row):
        # Replace inline calculation with shared score calculation
        return calculate_score(row)

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
        """Calculate the score for a given user."""
        # Fetch necessary data
        last_message = await self._get_last_message_time(user_id)
        messages_past_month = await self._get_messages_past_month(user_id)
        flags = await self.flag.get_user_activity_flags(user_id)

        # Create a DataFrame row for the user
        user_row = {
            "user_id": user_id,
            "last_message": last_message,
            "messages_past_month": messages_past_month,
            **flags
        }

        # Calculate the score using the same logic as _calculate_score
        score = self._calculate_score(user_row)

        # Update the final score in the database
        database.update_final_score(user_id, score)

        logger.info(f"Final score for user {user_id}: {score}")
        return score

    @commands.command(name="checkscore")
    async def check_score(self, ctx, user_id: str = None):
        """Command to check the score of a user by user ID."""
        if user_id is None:
            await ctx.send("Please provide a user ID.")
            return

        # Strip mention format if present
        if user_id.startswith('<@') and user_id.endswith('>'):
            user_id = user_id[2:-1]
            if user_id.startswith('!'):
                user_id = user_id[1:]
        try:
            user_id = int(user_id)
        except ValueError:
            await ctx.send("Invalid user ID format.")
            return

        start_time = datetime.datetime.now()
        logger.info(f"Recalculating score for user ID: {user_id}")

        # Recalculate the score dynamically using the new logic
        score = await self.calculate_score(user_id)
        logger.info(f"Dynamic score for user {user_id}: {score}")

        # Create a DataFrame for the user score
        user_score_df = pd.DataFrame({
            "user_id": [user_id],
            "score": [score],
            "sent_messages_after_joining": [await self.flag.sent_messages_after_joining(user_id)],
            "messaged_within_30_days": [await self.flag.messaged_within_x_days(user_id, 30)],
            "above_100_messages": [await self.flag.above_x_messages(user_id, 100)],
            "below_10_messages": [await self.flag.below_x_messages(user_id, 10)],
            "never_messaged": [await self.flag.never_messaged(user_id)],
            "no_role_assigned": [await self.flag.no_role_assigned(user_id)],
            "low_interaction_high_activity": [await self.flag.low_interaction_high_activity(user_id)]
        })

        # Convert the DataFrame to an image
        dataframe_to_image(user_score_df, filename="user_score.png")

        # Send the image
        await ctx.send(file=discord.File("user_score.png"))

        end_time = datetime.datetime.now()
        logger.info(f"Score recalculation completed in {end_time - start_time}")


async def setup(bot):
    await bot.add_cog(FlagScanner(bot))
    logger.info("FlagScanner cog added to bot")