import discord
from discord.ext import commands, tasks
import aiohttp
import os
import json
import re
import logging
from utils.constants import Emojis

logger = logging.getLogger('discord')

class YouTubeNotifierCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.yt_channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
        
        try:
            self.notify_channel_id = int(os.getenv("NOTIFY_CHANNEL_ID", 0))
        except ValueError:
            self.notify_channel_id = 0
            
        self.data_file = "last_video.json"
        self.last_video_id = self.load_last_video()
        
        if self.youtube_api_key and self.yt_channel_id and self.notify_channel_id != 0:
            self.check_new_videos.start()
            logger.info("YouTube Notifier Task started with ultra-fast RSS integration.")
        else:
            logger.warning("YouTube Notifier is disabled. Missing credentials in .env")

    def cog_unload(self):
        self.check_new_videos.cancel()

    def load_last_video(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    return data.get("last_video_id", None)
            except Exception:
                return None
        return None

    def save_last_video(self, video_id):
        try:
            with open(self.data_file, 'w') as f:
                json.dump({"last_video_id": video_id}, f)
        except Exception as e:
            logger.error(f"Error saving last video: {e}")

    # Ahora revisamos cada 1 minuto (60s) usando el feed RSS gratuito que consume 0 cuota de API
    @tasks.loop(minutes=1)
    async def check_new_videos(self):
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.yt_channel_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(rss_url) as response:
                    if response.status != 200:
                        return
                    
                    xml_data = await response.text()
                    
                    # Buscamos el ID del video ms reciente en el XML
                    match = re.search(r"<yt:videoId>(.*?)</yt:videoId>", xml_data)
                    if not match:
                        return
                        
                    video_id = match.group(1)
                    
                    # Si detectamos un video nuevo
                    if self.last_video_id and video_id != self.last_video_id:
                        
                        # Hacemos una peticin a la API de Videos (Cuesta 1 unidad en vez de 100) para ver si es directo o video
                        api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={self.youtube_api_key}"
                        async with session.get(api_url) as api_response:
                            if api_response.status == 200:
                                data = await api_response.json()
                                if data.get("items"):
                                    self.last_video_id = video_id
                                    self.save_last_video(video_id)
                                    
                                    video_info = data["items"][0]["snippet"]
                                    title = video_info["title"]
                                    live_status = video_info.get("liveBroadcastContent", "none")
                                    
                                    channel = self.bot.get_channel(self.notify_channel_id)
                                    if channel:
                                        if live_status == "live":
                                            msg = (f"@everyone 🔴 **¡ALERTA DE DIRECTO!** 🔴\n\n"
                                                   f"¡Dejen lo que estén haciendo! Angelus11 acaba de prender stream. "
                                                   f"Si no entras ahora, te vas a perder el chisme en vivo.\n\n"
                                                   f"**{title}**\nhttps://www.youtube.com/watch?v={video_id}")
                                        else:
                                            msg = (f"@everyone 🍿 **¡NUEVO VIDEO RECIÉN SALIDO DEL HORNO!** 🍿\n\n"
                                                   f"La espera ha terminado. Angelus11 acaba de bendecirnos con contenido fresco. "
                                                   f"Ve a darle amor, deja tu like y no te olvides de comentar.\n\n"
                                                   f"**{title}**\nhttps://www.youtube.com/watch?v={video_id}")
                                            
                                        await channel.send(msg)
                                        
                    elif not self.last_video_id:
                        # Primera ejecucin, solo guardar el ID
                        self.last_video_id = video_id
                        self.save_last_video(video_id)
                        
        except Exception as e:
            logger.error(f"Error checking YouTube RSS for new videos: {e}")

    @check_new_videos.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(YouTubeNotifierCog(bot))