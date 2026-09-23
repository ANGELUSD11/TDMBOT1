import discord
from discord.ext import commands
import os
import aiohttp
import asyncio
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException, RatelimitException, TimeoutException
from utils.constants import EmbedColors, Emojis

class QueryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")

    @commands.hybrid_command(name="yt", description="Search for a YouTube video")
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def yt(self, ctx: commands.Context, *, search_query: str = None):
        if not search_query:
            return await ctx.send(f"{Emojis.WARNING} **Incorrect usage.** Format: `>yt [search_query]`\nExample: `>yt python tutorial`")
            
        await ctx.defer() 
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {"part": "snippet", "q": search_query, "key": self.youtube_api_key, "type": "video", "maxResults": 1}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        if response.status == 403:
                            return await ctx.send(f"{Emojis.NO} YouTube API Error: Access Forbidden. Check your API Key or Quota limit.")
                        elif response.status == 429:
                            return await ctx.send(f"{Emojis.WARNING} YouTube API Error: Too many requests (Rate limited). Try again later.")
                        elif response.status >= 500:
                            return await ctx.send(f"{Emojis.NO} YouTube API Error: YouTube servers are currently experiencing issues.")
                        else:
                            return await ctx.send(f"{Emojis.NO} YouTube API Error: Received status code {response.status}.")

                    data = await response.json()
                    if not data.get('items'):
                        return await ctx.send(f"{Emojis.WARNING} No videos found for that query.")
                    
                    video = data['items'][0]
                    video_id = video['id']['videoId']
                    await ctx.send(f"https://www.youtube.com/watch?v={video_id}")
        except aiohttp.ClientError as e:
            await ctx.send(f"{Emojis.NO} Network error while trying to connect to YouTube: {str(e)}")
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An unexpected error occurred: {str(e)}")

    @commands.hybrid_command(name="search", description="Search the web using DuckDuckGo")
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def search(self, ctx: commands.Context, *, query: str = None):
        if not query:
            return await ctx.send(f"{Emojis.WARNING} **Incorrect usage.** Format: `>search [query]`\nExample: `>search history of rome`")
            
        await ctx.defer()
        
        from utils.cache import redis_cache
        cache_key = f"ddgs:text:{query.lower()}"
        
        cached_data = await redis_cache.get(cache_key)
        if cached_data:
            embed = discord.Embed(title=f"{Emojis.SEARCH} DuckDuckGo Search: {query}", color=EmbedColors.WARNING)
            embed.set_footer(text="⚡ Instantly fetched from Redis Cache")
            for res in cached_data:
                embed.add_field(
                    name=res.get("title", "No Title"),
                    value=f"{res.get('body', 'No Description')}...\n[Read more]({res.get('href', '#')})",
                    inline=False
                )
            return await ctx.send(embed=embed)

        def do_search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=3))
                
        try:
            results = await asyncio.to_thread(do_search)
            
            if not results:
                return await ctx.send(f"{Emojis.WARNING} No results found.")
                
            await redis_cache.set(cache_key, results, ttl=3600) # Cache for 1 hour
                
            embed = discord.Embed(title=f"{Emojis.SEARCH} DuckDuckGo Search: {query}", color=EmbedColors.WARNING)
            for res in results:
                embed.add_field(
                    name=res.get("title", "No Title"),
                    value=f"{res.get('body', 'No Description')}...\n[Read more]({res.get('href', '#')})",
                    inline=False
                )
            await ctx.send(embed=embed)
        except RatelimitException:
            await ctx.send(f"{Emojis.WARNING} DuckDuckGo rate limit reached. Please wait a bit before searching again.")
        except TimeoutException:
            await ctx.send(f"{Emojis.NO} DuckDuckGo search timed out. The server took too long to respond.")
        except DuckDuckGoSearchException as e:
            await ctx.send(f"{Emojis.NO} DuckDuckGo Search Error: {str(e)}")
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An unexpected error occurred during the web search: {str(e)}")

    @commands.hybrid_command(name="img", description="Search for an image using DuckDuckGo")
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def img(self, ctx: commands.Context, *, query: str = None):
        if not query:
            return await ctx.send(f"{Emojis.WARNING} **Incorrect usage.** Format: `>img [query]`\nExample: `>img beautiful landscape`")
            
        await ctx.defer()
        
        def do_img_search():
            with DDGS() as ddgs:
                return list(ddgs.images(query, max_results=1))
                
        try:
            results = await asyncio.to_thread(do_img_search)
            
            if not results:
                return await ctx.send(f"{Emojis.WARNING} No images found.")
                
            image_data = results[0]
            embed = discord.Embed(
                title=f"{Emojis.IMAGE} {image_data.get('title', query)}",
                url=image_data.get("url", "#"),
                color=EmbedColors.WARNING
            )
            embed.set_image(url=image_data.get("image"))
            embed.set_footer(text=f"Source: {image_data.get('source', 'DuckDuckGo')}")
            
            await ctx.send(embed=embed)
        except RatelimitException:
            await ctx.send(f"{Emojis.WARNING} DuckDuckGo rate limit reached. Please wait a bit before searching again.")
        except TimeoutException:
            await ctx.send(f"{Emojis.NO} DuckDuckGo image search timed out. The server took too long to respond.")
        except DuckDuckGoSearchException as e:
            await ctx.send(f"{Emojis.NO} DuckDuckGo Search Error: {str(e)}")
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An unexpected error occurred during the image search: {str(e)}")

async def setup(bot):
    await bot.add_cog(QueryCog(bot))
