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
            
        self.data_file = "notified_videos.json"
        self.notified_videos = self.load_notified_videos()
        
        if self.youtube_api_key and self.yt_channel_id and self.notify_channel_id != 0:
            self.check_new_videos.start()
            logger.info("YouTube Notifier Task started with ultra-fast RSS integration.")
        else:
            logger.warning("YouTube Notifier is disabled. Missing credentials in .env")

    def cog_unload(self):
        self.check_new_videos.cancel()

    def load_notified_videos(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    return data.get("notified_videos", [])
            except Exception:
                return []
        # Migracion desde el archivo viejo
        old_data_file = "last_video.json"
        if os.path.exists(old_data_file):
            try:
                with open(old_data_file, 'r') as f:
                    data = json.load(f)
                    last_id = data.get("last_video_id")
                    if last_id:
                        return [last_id]
            except Exception:
                pass
        return []

    def save_notified_videos(self, video_id):
        if video_id not in self.notified_videos:
            self.notified_videos.append(video_id)
            # Mantener solo los ultimos 15 videos para no llenar el json
            if len(self.notified_videos) > 15:
                self.notified_videos.pop(0)
                
        try:
            with open(self.data_file, 'w') as f:
                json.dump({"notified_videos": self.notified_videos}, f)
        except Exception as e:
            logger.error(f"Error saving notified videos: {e}")

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
                    
                    # Si detectamos un video nuevo que NO esta en nuestra lista de notificados
                    if self.notified_videos and video_id not in self.notified_videos:
                        
                        api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={self.youtube_api_key}"
                        async with session.get(api_url) as api_response:
                            if api_response.status == 200:
                                data = await api_response.json()
                                if data.get("items"):
                                    self.save_notified_videos(video_id)
                                    
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
                                        elif live_status == "none":
                                            # Es un video normal (o un VOD, pero como no estaba en la lista, es un video real)
                                            msg = (f"@everyone 🍿 **¡NUEVO VIDEO RECIÉN SALIDO DEL HORNO!** 🍿\n\n"
                                                   f"La espera ha terminado. Angelus11 acaba de bendecirnos con contenido fresco. "
                                                   f"Ve a darle amor, deja tu like y no te olvides de comentar.\n\n"
                                                   f"**{title}**\nhttps://www.youtube.com/watch?v={video_id}")
                                            
                                        await channel.send(msg)
                                        
                    elif not self.notified_videos:
                        # Primera ejecucin, solo guardar el ID sin notificar
                        self.save_notified_videos(video_id)
                        
        except Exception as e:
            logger.error(f"Error checking YouTube RSS for new videos: {e}")

    @check_new_videos.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(YouTubeNotifierCog(bot))