import discord
from discord.ext import commands
from utils.constants import EmbedColors, Emojis, BotConfig

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="madewith", description="Technical info about the bot")
    async def madewith(self, ctx: commands.Context):
        embed = discord.Embed(
            title=f'{Emojis.BOT} **Created with Python by {BotConfig.AUTHOR}**\n\ndiscord.py V2', 
            description=f'Website: {BotConfig.WEBSITE}\nSource code: {BotConfig.GITHUB_URL}\n\nHosted properly on professional environments.', 
            color=EmbedColors.INFO
        )
        embed.set_thumbnail(url='https://images.opencollective.com/discordpy/25fb26d/logo/256.png')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", description="Show a user's avatar")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"Avatar of {member.display_name}", color=EmbedColors.DEFAULT)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="spotify", description="Check what you or another user is listening to")
    async def spotify(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        activity = next((a for a in member.activities if isinstance(a, discord.Spotify)), None)

        if activity:
            embed = discord.Embed(
                title=f'{member.display_name} is listening to {activity.title}', 
                description=f'Artist: {activity.artist}\nAlbum: {activity.album}', 
                color=activity.color
            )
            embed.set_thumbnail(url=activity.album_cover_url)
            embed.add_field(name='Duration', value=str(activity.duration), inline=True)
            embed.add_field(name='Listen on Spotify', value=f'[Link]({activity.track_url})', inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{Emojis.NO} {member.display_name} is not listening to Spotify right now.")

    @commands.hybrid_command(name="help", description="Shows the list of available commands")
    async def help_command(self, ctx: commands.Context):
        embed = discord.Embed(
            title=f'**TDMBOT | Command List {BotConfig.VERSION}**',
            description=(
                f"Hello! I am a professional bot developed by **{BotConfig.AUTHOR}**. "
                "My prefix is > and I also fully support Slash Commands /.\n\n"
                "**🌐 Web & AI:**\n"
                "`>search` - Search the web with DuckDuckGo\n"
                "`>img` - Search for images\n"
                "`>wiki` - Search articles on Wikipedia\n"
                "`>chat` - Ask Gemini Flash AI anything\n"
                "`>smart` - Ask Gemini, backed by real-time internet search\n"
                "`>programmer` - Expert AI coding assistant and mentor\n"
                "`>translate` - Translate text to any language\n"
                "`>ocr` - Extract text from attached images\n\n"
                "**😂 Entertainment:**\n"
                ">meme / >shitpost / >cat - Random Reddit memes\n\n"
                "**🎙️ Voice Channel:**\n"
                ">join / >leave - Connect or disconnect\n"
                ">ask - Make me speak text in the VC using TTS\n\n"
                "**🔧 Utility:**\n"
                ">avatar - View a user's profile picture\n"
                ">spotify - View what a user is listening to\n"
                ">binary - Convert text to binary and vice versa\n"
                ">madewith - Technical info about the bot\n\n"
                f"Author: [{BotConfig.AUTHOR}]({BotConfig.WEBSITE}) | [GitHub]({BotConfig.GITHUB_URL})"
            ),
            color=EmbedColors.SUCCESS
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InfoCog(bot))
