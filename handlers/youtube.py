import yt_dlp

import utils
from metadata.youtubesong import YoutubeSong

def search_youtube_and_add_to_queue(reverb, query, limit=1):
    is_url = utils.is_url(query)
    is_playlist = "list=" in query or "/sets/" in query

    ytdl_options = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": not is_playlist
    }

    yt_query = f"ytsearch{limit}:{query}" if not is_url else query

    skip_first = False

    if is_url:
        # parse first video if it's a playlist for quicker playback
        with yt_dlp.YoutubeDL({
            **ytdl_options,
            "noplaylist": True
        }) as yt:
            info = yt.extract_info(yt_query, download=False)
            entries = info.get("entries", [info])

            for entry in entries:
                reverb.metadata_queue.append(YoutubeSong(entry))

        skip_first = True

    with yt_dlp.YoutubeDL(ytdl_options) as yt:
        info = yt.extract_info(yt_query, download=False)
        entries = info.get("entries", [info])

        for entry in entries:
            if skip_first:
                # skip first video as it's already been parsed before
                skip_first = False
                continue

            reverb.metadata_queue.append(YoutubeSong(entry))

def get_source(url, output_path):
    ytdl_options = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "0",
        }],
    }

    with yt_dlp.YoutubeDL(ytdl_options) as ytdlp:
        ytdlp.download([url])
