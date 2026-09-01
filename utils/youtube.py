from yt_dlp import YoutubeDL
import asyncio
import logging
from utils.models import Song

log = logging.getLogger(__name__)

#options/settings for YoutubeDL and ffmpeg.
yt_dl_options = {"format": "bestaudio/best"}
ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.30"'}



#this function searches for a YouTube link based on the search criteria provided by the user who submits the call
#If they provide a link, it sends that link off to have the audio extracted.
async def search_YT(search):
        if "https://www.youtube.com/watch?v=" in search or "https://youtu.be/" in search:
            log.info("search_YT, if")
            return search
        else:
            log.info("search_YT, else")
            loop = asyncio.get_running_loop()
            with YoutubeDL(yt_dl_options) as ydl:
                info = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(f"ytsearch:{search}", download=False)
                )
                return info['entries'][0]['webpage_url']


#extracts audio, thumbnail, title, from the YouTube link provided by the Search_YT function.
#Note: the search_YT function returns to the play function, which then uses this function to extract the audio.
async def extract_YT(url):
    loop = asyncio.get_running_loop()
    with YoutubeDL(yt_dl_options) as ydl:
        try:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(url, download=False)
            )
        except:
            return False
    return Song(
        link=info.get("webpage_url", ""),
        thumbnail=info["thumbnails"][-1]["url"],
        source=info["url"],
        title=info["title"],
    )