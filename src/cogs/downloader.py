import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio
from utils.constants import EmbedColors, Emojis

class DownloaderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

    @commands.hybrid_command(name="dl", description="Download a video from YouTube, TikTok, Twitter, etc.")
    async def dl(self, ctx: commands.Context, url: str):
        await ctx.defer()
        
        # Options optimized for Discord (25MB limit) and avoiding YouTube Bot Protection
        ydl_opts = {
            'format': 'b[filesize<25M]/w', # Try best under 25MB, else worst
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            # Workaround for YouTube "Sign in to confirm you're not a bot"
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

        def download_video():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info), info.get('title', 'Video')

        try:
            file_path, title = await asyncio.to_thread(download_video)
            
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 25 * 1024 * 1024: # 25MB limit strictly enforced
                        return await ctx.send(f"{Emojis.WARNING} The video '{title}' is too large to send over Discord (limit is 25MB).")
                    
                    file = discord.File(file_path)
                    await ctx.send(content=f"{Emojis.YES} **{title}**", file=file)
                finally:
                    # STRICT CLEANUP: Always delete the file even if upload fails
                    if os.path.exists(file_path):
                        os.remove(file_path)
            else:
                await ctx.send(f"{Emojis.NO} Could not save the video.")
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Sign in" in error_msg or "bot" in error_msg:
                 await ctx.send(f"{Emojis.NO} YouTube is blocking the download due to bot protection (Cookies error).")
            elif "too large" in error_msg.lower():
                 await ctx.send(f"{Emojis.WARNING} The video is too large or has no formats under 25MB.")
            else:
                 await ctx.send(f"{Emojis.NO} Error downloading video: Make sure the URL is valid.")
            print(f"yt-dlp Error: {error_msg}")
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An unexpected error occurred while downloading.")
            print(f"Download Error: {e}")

async def setup(bot):
    await bot.add_cog(DownloaderCog(bot))
