import discord
from discord.ext import commands
import asyncpraw
import asyncprawcore
import os
import random
from utils.constants import EmbedColors, Emojis

class RedditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reddit = asyncpraw.Reddit(
            client_id=os.getenv("CLIENT_ID"),
            client_secret=os.getenv("CLIENT_SECRET"),
            user_agent="discord:tdmbot:v1.0 (by u/Angelus11)"
        )

    async def fetch_meme(self, ctx, subreddit_name):
        await ctx.defer()
        try:
            subreddit = await self.reddit.subreddit(subreddit_name)
            submissions = [post async for post in subreddit.hot(limit=50) if not post.is_video and not post.over_18]
            
            if not submissions:
                return await ctx.send(f"{Emojis.WARNING} No valid memes found in r/{subreddit_name}.")
                
            post = random.choice(submissions)
            embed = discord.Embed(title=post.title, url=f"https://reddit.com{post.permalink}", color=EmbedColors.WARNING)
            embed.set_image(url=post.url)
            embed.set_footer(text=f"👍 {post.score} | 💬 {post.num_comments} | r/{subreddit_name}")
            await ctx.send(embed=embed)
            
        except asyncprawcore.exceptions.Forbidden:
            await ctx.send(f"{Emojis.NO} Reddit API Error: Access to r/{subreddit_name} is forbidden (it might be private).")
        except asyncprawcore.exceptions.NotFound:
            await ctx.send(f"{Emojis.NO} Reddit API Error: The subreddit r/{subreddit_name} was not found.")
        except asyncprawcore.exceptions.TooManyRequests:
            await ctx.send(f"{Emojis.WARNING} Reddit API Error: Rate limited by Reddit. Please try again later.")
        except asyncprawcore.exceptions.ServerError:
            await ctx.send(f"{Emojis.NO} Reddit API Error: Reddit servers are currently experiencing issues (500 Internal Server Error).")
        except asyncprawcore.exceptions.ResponseException as e:
            await ctx.send(f"{Emojis.NO} Reddit API Error: Received bad response. Check Railway logs for exact HTTP error.")
            import traceback
            traceback.print_exc()
            try:
                print(f"Reddit HTTP Status: {e.response.status}")
                print(f"Reddit HTTP Body: {await e.response.text()}")
            except:
                pass
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An unexpected error occurred while fetching the meme: {str(e)}")
            print(f"Reddit API Error: {e}")

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
