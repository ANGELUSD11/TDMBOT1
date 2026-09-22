import discord
from discord.ext import commands
import os
import google.generativeai as genai
from gtts import gTTS
import asyncio
import uuid
from langdetect import detect, LangDetectException
from PIL import Image
from io import BytesIO
from duckduckgo_search import DDGS
from utils.constants import Emojis

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            print("WARNING: GEMINI_API_KEY not found in environment variables.")
            self.model = None

    async def _process_tts(self, ctx, response_text):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            audio_file = f"temp_tts_{uuid.uuid4()}.mp3"
            
            def generate_tts():
                try:
                    detected_lang = detect(response_text)
                    try:
                        tts = gTTS(text=response_text, lang=detected_lang)
                    except ValueError:
                        tts = gTTS(text=response_text, lang='en')
                except LangDetectException:
                    tts = gTTS(text=response_text, lang='en')
                    
                tts.save(audio_file)
            
            await asyncio.to_thread(generate_tts)
            
            try:
                if not voice_client.is_playing():
                    voice_client.play(
                        discord.FFmpegPCMAudio(audio_file),
                        after=lambda e: os.remove(audio_file) if os.path.exists(audio_file) else None
                    )
                else:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
            except Exception as play_error:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                print(f"Error playing audio: {play_error}")

    @commands.hybrid_command(name="chat", description="Chat with Gemini Flash AI (Supports Images)")
    async def chat(self, ctx: commands.Context, *, message: str = None):
        if not self.model:
            return await ctx.send(f"{Emojis.NO} Gemini API is not configured. Missing GEMINI_API_KEY.")
            
        if not message and not ctx.message.attachments:
            return await ctx.send(f"{Emojis.WARNING} You must provide a message or an image to chat with Gemini.")

        await ctx.defer()
        
        try:
            content_to_send = []
            if message:
                content_to_send.append(message)
                
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    image_bytes = await attachment.read()
                    image = Image.open(BytesIO(image_bytes))
                    content_to_send.append(image)
                else:
                    return await ctx.send(f"{Emojis.WARNING} The attached file is not a supported image format.")
                    
            response = await self.model.generate_content_async(content_to_send)
            response_text = response.text
            
            if len(response_text) <= 2000:
                await ctx.send(response_text)
            else:
                for i in range(0, len(response_text), 1990):
                    await ctx.send(response_text[i:i+1990])
                    
            await self._process_tts(ctx, response_text)
                    
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An error occurred while communicating with Gemini.")
            print(f"Gemini API Error: {e}")

    @commands.hybrid_command(name="smart", description="Ask Gemini, backed by real-time web search")
    async def smart(self, ctx: commands.Context, *, question: str):
        if not self.model:
            return await ctx.send(f"{Emojis.NO} Gemini API is not configured.")

        await ctx.defer()
        
        try:
            def do_search():
                with DDGS() as ddgs:
                    return list(ddgs.text(question, max_results=5))
                    
            try:
                results = await asyncio.to_thread(do_search)
            except Exception:
                results = []
                
            context = "Web Search Results:\n"
            if results:
                for idx, res in enumerate(results):
                    context += f"{idx+1}. Title: {res.get('title')}\nSnippet: {res.get('body')}\nURL: {res.get('href')}\n\n"
            else:
                context += "No web results found.\n"
                
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_path = os.path.join(current_dir, "..", "prompts", "smart_search.md")
            
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
                
            prompt = prompt_template.format(context=context, question=question)
            
            response = await self.model.generate_content_async(prompt)
            response_text = response.text
            
            if len(response_text) <= 2000:
                await ctx.send(response_text)
            else:
                for i in range(0, len(response_text), 1990):
                    await ctx.send(response_text[i:i+1990])
                    
            await self._process_tts(ctx, response_text)
                    
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An error occurred while communicating with Gemini.")
            print(f"Gemini API Error: {e}")

    @commands.hybrid_command(name="programmer", description="Expert AI coding assistant and mentor")
    async def programmer(self, ctx: commands.Context, *, question: str):
        if not self.model:
            return await ctx.send(f"{Emojis.NO} Gemini API is not configured.")

        await ctx.defer()
        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_path = os.path.join(current_dir, "..", "prompts", "programmer.md")
            
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
                
            prompt = prompt_template.format(question=question)
            
            response = await self.model.generate_content_async(prompt)
            response_text = response.text
            
            if len(response_text) <= 2000:
                await ctx.send(response_text)
            else:
                for i in range(0, len(response_text), 1990):
                    await ctx.send(response_text[i:i+1990])
                    
            await self._process_tts(ctx, response_text)
                    
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An error occurred while communicating with Gemini.")
            print(f"Gemini API Error: {e}")

async def setup(bot):
    await bot.add_cog(AICog(bot))
