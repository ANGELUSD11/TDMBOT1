import discord
from discord.ext import commands
from deep_translator import MyMemoryTranslator
import wikipedia
import asyncio
from langdetect import detect
from deep_translator import MyMemoryTranslator
from utils.constants import EmbedColors, Emojis

class UtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="translate", description="Translate text to a specific language")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def translate(self, ctx: commands.Context, lang: str = None, *, text: str = None):
        if not lang or not text:
            msg = (
                f"{Emojis.WARNING} **Incorrect usage.**\n"
                f"Format: `>translate [language] [text]`\n\n"
                f"**Examples:**\n"
                f"`>translate en Hola mundo` (Translates to English)\n"
                f"`>translate es Hello world` (Translates to Spanish)\n"
                f"`>translate fr Good morning` (Translates to French)\n\n"
                f"**Common languages:**\n"
                f"`en` (English), `es` (Spanish), `fr` (French), `de` (German), `it` (Italian), `pt` (Portuguese), `ja` (Japanese), `ru` (Russian)."
            )
            return await ctx.send(msg)
            
        await ctx.defer()
        
        from utils.cache import redis_cache
        cache_key = f"translate:{lang.lower()}:{text}"
        
        cached_data = await redis_cache.get(cache_key)
        if cached_data:
            embed = discord.Embed(title=f"{Emojis.YES} Translation", color=EmbedColors.SUCCESS)
            embed.add_field(name="Original", value=text[:1024], inline=False)
            embed.add_field(name=f"Translated ({lang})", value=cached_data[:1024], inline=False)
            embed.set_footer(text="⚡ Instantly fetched from Redis Cache")
            return await ctx.send(embed=embed)
            
        try:
            lang_map = {
                'en': 'en-US', 'es': 'es-ES', 'fr': 'fr-FR', 'de': 'de-DE',
                'it': 'it-IT', 'pt': 'pt-PT', 'ru': 'ru-RU', 'ja': 'ja-JP',
                'zh': 'zh-CN', 'ar': 'ar-SA'
            }
            target_lang = lang_map.get(lang.lower(), lang)
            
            try:
                source_lang = detect(text)
                source_lang = lang_map.get(source_lang, source_lang)
            except:
                source_lang = 'es-ES'

            translated = await asyncio.to_thread(
                MyMemoryTranslator(source=source_lang, target=target_lang).translate, 
                text
            )
            
            await redis_cache.set(cache_key, translated, ttl=86400) # Cache for 24 hours
            
            embed = discord.Embed(title=f"{Emojis.YES} Translation", color=EmbedColors.SUCCESS)
            embed.add_field(name="Original", value=text[:1024], inline=False)
            embed.add_field(name=f"Translated ({lang})", value=translated[:1024], inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An error occurred during translation. Check if the language code is valid.").")

    @commands.hybrid_command(name="wiki", description="Search Wikipedia")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def wiki(self, ctx: commands.Context, *, query: str = None):
        if not query:
            return await ctx.send(f"{Emojis.WARNING} **Incorrect usage.** Format: `>wiki [search term]`\nExample: `>wiki Python`")
            
        await ctx.defer()
        
        def fetch_wiki():
            wikipedia.set_lang('es') 
            try:
                summary = wikipedia.summary(query, sentences=3)
                page = wikipedia.page(query)
                return summary, page.url
            except wikipedia.exceptions.DisambiguationError:
                return "The query is ambiguous, please be more specific.", None
            except wikipedia.exceptions.PageError:
                return "No articles found for that query.", None
            except Exception as e:
                return f"Error: {e}", None

        summary, url = await asyncio.to_thread(fetch_wiki)
        
        if url:
            embed = discord.Embed(title=f"{Emojis.SEARCH} Wikipedia: {query}", description=summary, url=url, color=EmbedColors.DEFAULT)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{Emojis.WARNING} {summary}")

async def setup(bot):
    await bot.add_cog(UtilsCog(bot))
