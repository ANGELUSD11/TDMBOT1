import discord
from discord.ext import commands, tasks
import os
import datetime
import logging
from utils.constants import Emojis
from utils.cache import redis_cache

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

    @commands.hybrid_command(name="setbday", description="Set your birthday so the bot can congratulate you! (Format: DD/MM)")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def setbday(self, ctx: commands.Context, date: str):
        try:
            day_str, month_str = date.split('/')
            day = int(day_str)
            month = int(month_str)
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError
        except ValueError:
            return await ctx.send(f"{Emojis.WARNING} Invalid format. Please use DD/MM (e.g., 15/07 for July 15).")
            
        if not redis_cache.redis:
            return await ctx.send(f"{Emojis.NO} Database is offline. Cannot save your birthday right now.")
            
        bday_key = f"{month:02d}-{day:02d}"
        user_id = str(ctx.author.id)
        
        # Guardar en Redis
        await redis_cache.set(f"user:{user_id}:bday", bday_key, ttl=None)
        await redis_cache.set(f"user:{user_id}:channel", str(ctx.channel.id), ttl=None)
        
        # Añadir al índice de fechas
        users_on_this_day = await redis_cache.get(f"birthdays:{bday_key}") or []
        if user_id not in users_on_this_day:
            users_on_this_day.append(user_id)
            await redis_cache.set(f"birthdays:{bday_key}", users_on_this_day, ttl=None)
            
        await ctx.send(f"{Emojis.PARTY} Awesome! I've saved your birthday as **{day:02d}/{month:02d}** and I'll remind everyone in this channel!")

    @tasks.loop(minutes=1)
    async def birthday_reminder(self):
        now = datetime.datetime.now()
        
        # Recordatorio nativo (Dueño)
        if (now.day == self.BIRTH_DAY and
            now.month == self.BIRTH_MONTH and
            now.hour == self.BIRTH_HOUR and
            now.minute == self.BIRTH_MINUTE):
            
            if self.channel_id != 0:
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    age = now.year - self.BIRTH_YEAR
                    await channel.send(f"{Emojis.PARTY} @everyone Today is Angelus11's birthday, congratulate him for turning {age}! {Emojis.PARTY}")
                    
        # Recordatorio comunitario
        if now.hour == 12 and now.minute == 0:
            if redis_cache.redis:
                today_key = f"{now.month:02d}-{now.day:02d}"
                birthday_users = await redis_cache.get(f"birthdays:{today_key}") or []
                
                for uid in birthday_users:
                    channel_id_str = await redis_cache.get(f"user:{uid}:channel")
                    if channel_id_str:
                        channel = self.bot.get_channel(int(channel_id_str))
                        if channel:
                            await channel.send(f"🎉 **¡Feliz Cumpleaños!** 🎉\nHoy es el cumpleaños de <@{uid}>. ¡Vayan a felicitarlo/a! 🎂🎁")

    @birthday_reminder.before_loop
    async def before_birthday_reminder(self):
        await self.bot.wait_until_ready()
        logger.info("Birthday reminder is ready.")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
