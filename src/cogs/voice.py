import discord
from discord.ext import commands
import asyncio
import os
import uuid
from gtts import gTTS
from langdetect import detect, LangDetectException
from utils.constants import Emojis

class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tts_locks = {}

    @commands.hybrid_command(name="join", description="Join the voice channel")
    async def join(self, ctx: commands.Context):
        if not ctx.author.voice:
            return await ctx.send(f"{Emojis.NO} You are not connected to a voice channel.")
            
        if ctx.voice_client:
            return await ctx.send(f"{Emojis.WARNING} I am already in a voice channel.")

        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"{Emojis.YES} Connected to {channel.name}.")

    @commands.hybrid_command(name="leave", description="Leave the voice channel")
    async def leave(self, ctx: commands.Context):
        if not ctx.voice_client:
            return await ctx.send(f"{Emojis.WARNING} I am not connected to any voice channel.")
            
        await ctx.voice_client.disconnect()
        await ctx.send(f"{Emojis.YES} Disconnected from the voice channel.")

    @commands.hybrid_command(name="ask", description="Speak text in the voice channel (useful if you have no mic)")
    async def ask(self, ctx: commands.Context, *, text: str):
        if not ctx.author.voice:
            return await ctx.send(f"{Emojis.NO} You need to be in a voice channel to use this command.")

        voice_client = ctx.voice_client
        if not voice_client:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
        
        await ctx.defer()
        
        audio_file = f"temp_ask_{uuid.uuid4()}.mp3"
        
        def generate_ask_tts():
            try:
                detected_lang = detect(text)
                try:
                    tts = gTTS(text=text, lang=detected_lang)
                except ValueError:
                    tts = gTTS(text=text, lang='en')
            except LangDetectException:
                tts = gTTS(text=text, lang='en')
                
            tts.save(audio_file)

        await asyncio.to_thread(generate_ask_tts)
        
        try:
            # High-load race condition fix: Use a lock per guild to queue TTS audio
            if ctx.guild.id not in self.tts_locks:
                self.tts_locks[ctx.guild.id] = asyncio.Lock()
                
            async with self.tts_locks[ctx.guild.id]:
                # Wait for any currently playing audio to finish naturally
                while voice_client.is_playing():
                    await asyncio.sleep(0.5)

                voice_client.play(
                    discord.FFmpegPCMAudio(audio_file),
                    after=lambda e: os.remove(audio_file) if os.path.exists(audio_file) else None
                )
        except Exception as play_error:
            if os.path.exists(audio_file):
                os.remove(audio_file)
            print(f"Error playing audio in ask: {play_error}")
        
        await ctx.send(f"{Emojis.SPEECH} **{ctx.author.display_name} says:** {text}")

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
