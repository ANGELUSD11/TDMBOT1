import discord
from discord.ext import commands
import aiohttp
from utils.constants import EmbedColors, Emojis

class RedditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_meme(self, ctx, subreddit_name):
        await ctx.defer()
        
        # meme-api.com expects a single subreddit or multiple separated by commas
        # If passed with '+' (e.g. memes+dankmemes), we replace with commas
        api_sub = subreddit_name.replace('+', ',')
        url = f"https://meme-api.com/gimme/{api_sub}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        embed = discord.Embed(title=data.get('title', 'Meme'), url=data.get('postLink'), color=EmbedColors.WARNING)
                        embed.set_image(url=data.get('url'))
                        embed.set_footer(text=f"👍 {data.get('ups', 0)} | r/{data.get('subreddit', subreddit_name)}")
                        await ctx.send(embed=embed)
                    elif response.status == 404:
                        await ctx.send(f"{Emojis.WARNING} No memes found in r/{subreddit_name}.")
                    else:
                        await ctx.send(f"{Emojis.NO} API Error: Received status {response.status} from meme-api.")
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An unexpected error occurred while fetching the meme.")
            print(f"Meme API Error: {e}")

    @commands.hybrid_command(name="meme", description="Fetches a random meme from Reddit")
    async def meme(self, ctx: commands.Context):
        await self.fetch_meme(ctx, "memes+dankmemes+me_irl")

    @commands.hybrid_command(name="shitpost", description="Fetches a random shitpost from Reddit")
    async def shitpost(self, ctx: commands.Context):
        await self.fetch_meme(ctx, "shitposting")
        
    @commands.hybrid_command(name="cat", description="Fetches a random cat image from Reddit")
    async def cat(self, ctx: commands.Context):
        await self.fetch_meme(ctx, "cats+catpictures")

async def setup(bot):
    await bot.add_cog(RedditCog(bot))
