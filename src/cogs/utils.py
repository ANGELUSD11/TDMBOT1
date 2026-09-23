import discord
from discord.ext import commands
import wikipedia
import asyncio
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
            import os
            from google import genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return await ctx.send(f"{Emojis.NO} Translation failed: GEMINI_API_KEY is missing.")
                
            client = genai.Client(api_key=api_key)
            prompt = f"You are a professional translator. Translate the following text to the language code/name '{lang}'. Output ONLY the translated text, without quotes, explanations, or original text. Maintain the original tone. Text to translate: {text}"
            
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            translated = response.text.strip()
            
            await redis_cache.set(cache_key, translated, ttl=86400) # Cache for 24 hours
            
            embed = discord.Embed(title=f"{Emojis.YES} Translation", color=EmbedColors.SUCCESS)
            embed.add_field(name="Original", value=text[:1024], inline=False)
            embed.add_field(name=f"Translated ({lang})", value=translated[:1024], inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An error occurred during translation. Check if your API Key is valid or try again later.")
            print(f"Translation error: {e}")

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

    @commands.hybrid_command(name="langs", description="List all supported language prefixes for translation")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def langs(self, ctx: commands.Context):
        msg = (
            "**Supported Language Prefixes for `>translate`**\n\n"
            "🇬🇧 `en` - English\n"
            "🇪🇸 `es` - Spanish (Español)\n"
            "🇫🇷 `fr` - French (Français)\n"
            "🇩🇪 `de` - German (Deutsch)\n"
            "🇮🇹 `it` - Italian (Italiano)\n"
            "🇵🇹 `pt` - Portuguese (Português)\n"
            "🇷🇺 `ru` - Russian (Русский)\n"
            "🇯🇵 `ja` - Japanese (日本語)\n"
            "🇨🇳 `zh` - Chinese (中文)\n"
            "🇰🇷 `ko` - Korean (한국어)\n"
            "🇸🇦 `ar` - Arabic (العربية)\n"
            "🇳🇱 `nl` - Dutch (Nederlands)\n"
            "🇹🇷 `tr` - Turkish (Türkçe)\n"
            "🇮🇳 `hi` - Hindi (हिन्दी)\n"
            "🇮🇩 `id` - Indonesian (Bahasa Indonesia)\n"
            "🇵🇱 `pl` - Polish (Polski)\n"
            "🇻🇳 `vi` - Vietnamese (Tiếng Việt)\n\n"
            "**Example:** `>translate ko Hello friend`"
        )
        embed = discord.Embed(description=msg, color=EmbedColors.INFO)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilsCog(bot))
