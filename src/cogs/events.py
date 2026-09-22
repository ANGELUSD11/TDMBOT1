import discord
from discord.ext import commands, tasks
import os
import datetime
import logging
from utils.constants import Emojis

logger = logging.getLogger('discord')

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.server_id = int(os.getenv("SERVER_ID", 0))
            self.channel_id = int(os.getenv("CHANNEL_ID", 0))
        except ValueError:
            self.server_id = 0
            self.channel_id = 0
            
        self.BIRTH_DAY = int(os.getenv("BIRTH_DAY", 15))
        self.BIRTH_MONTH = int(os.getenv("BIRTH_MONTH", 7))
        self.BIRTH_YEAR = int(os.getenv("BIRTH_YEAR", 2005))
        self.BIRTH_HOUR = 12
        self.BIRTH_MINUTE = 0
        
        self.birthday_reminder.start()

    def cog_unload(self):
        self.birthday_reminder.cancel()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == self.server_id and self.channel_id != 0:
            channel = member.guild.get_channel(self.channel_id)
            if channel:
                await channel.send(f"{Emojis.PARTY} {member.mention}, welcome to the server! :D")

    @tasks.loop(minutes=1)
    async def birthday_reminder(self):
        now = datetime.datetime.now()
        if (now.day == self.BIRTH_DAY and
            now.month == self.BIRTH_MONTH and
            now.hour == self.BIRTH_HOUR and
            now.minute == self.BIRTH_MINUTE):
            
            if self.channel_id != 0:
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    age = now.year - self.BIRTH_YEAR
                    await channel.send(f"{Emojis.PARTY} @everyone Today is Angelus's birthday, congratulate him for turning {age}! {Emojis.PARTY}")
                    
    @birthday_reminder.before_loop
    async def before_birthday_reminder(self):
        await self.bot.wait_until_ready()
        logger.info("Birthday reminder is ready.")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
