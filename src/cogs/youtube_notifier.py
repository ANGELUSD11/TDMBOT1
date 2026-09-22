import discord
from discord.ext import commands, tasks
import aiohttp
import os
import json
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
            
        # Utilizamos un archivo temporal local persistente
        self.data_file = "last_video.json"
        self.last_video_id = self.load_last_video()
        
        if self.youtube_api_key and self.yt_channel_id and self.notify_channel_id != 0:
            self.check_new_videos.start()
            logger.info("YouTube Notifier Task started.")
        else:
            logger.warning("YouTube Notifier is disabled. Missing YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID, or NOTIFY_CHANNEL_ID in .env")

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

    # Check every 15 minutes to save quota limits
    @tasks.loop(minutes=15)
    async def check_new_videos(self):
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "channelId": self.yt_channel_id,
            "order": "date",
            "maxResults": 1,
            "type": "video",
            "key": self.youtube_api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("items"):
                            latest_video = data["items"][0]
                            video_id = latest_video["id"]["videoId"]
                            
                            # If we detect a new video
                            if self.last_video_id and video_id != self.last_video_id:
                                self.last_video_id = video_id
                                self.save_last_video(video_id)
                                
                                channel = self.bot.get_channel(self.notify_channel_id)
                                if channel:
                                    title = latest_video["snippet"]["title"]
                                    live_status = latest_video["snippet"].get("liveBroadcastContent", "none")
                                    
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
                                # On first execution, just save the latest ID without notifying
                                self.last_video_id = video_id
                                self.save_last_video(video_id)
        except Exception as e:
            logger.error(f"Error checking YouTube for new videos: {e}")

    @check_new_videos.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(YouTubeNotifierCog(bot))
