import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import logging
from keep_alive import keep_alive

# Setup logging properly
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('discord')

load_dotenv()

from utils.cache import redis_cache

class ProfessionalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.presences = True
        intents.members = True
        
        super().__init__(
            command_prefix=commands.when_mentioned_or('>'),
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        await redis_cache.connect()
            
        # Load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Loaded Cog: {filename}')
                except Exception as e:
                    logger.error(f'Failed to load {filename}: {e}')
        
        # Sync slash commands
        await self.tree.sync()

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        activity = discord.Activity(type=discord.ActivityType.watching, name='TDMBOT1')
        await self.change_presence(activity=activity)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"⚠️ **Oops! Missing information.** Please provide the required argument: `{error.param.name}`")
        elif isinstance(error, commands.MissingRequiredAttachment) or 'missing an attachment' in str(error):
            await ctx.send(f"{Emojis.WARNING} **Oops! Missing image.** Please attach an image to the message.")
        elif isinstance(error, commands.CommandNotFound):
            pass # Ignore unknown commands to prevent spam
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ **Hold on!** This command is on cooldown. Try again in `{error.retry_after:.1f}s`.", delete_after=5)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You do not have permission to use this command.")
        elif isinstance(error, commands.MemberNotFound) or isinstance(error, commands.UserNotFound):
            await ctx.send(f"❓ **User not found.** I couldn't find anyone matching that name in the server.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"⚠️ **Invalid input.** Please check the spelling or format.")
        else:
            logger.error(f'Ignoring exception in command {ctx.command}: {error}')

if __name__ == '__main__':
    keep_alive() # Run the background web server
    bot = ProfessionalBot()
    bot.run(os.getenv('DISCORD_TOKEN'), log_handler=None)


