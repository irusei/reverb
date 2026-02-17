import yt_dlp

from reverb_types.ytvideo import YTVideo

def search_youtube(query, limit=1):
    ytdl_options = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True
    }

    yt_query = f"ytsearch{limit}:{query}"
    if "https://" in query or "http://" in query:
        yt_query = query

    if "list=" in query:
        ytdl_options["extract_flat"] = False

    with yt_dlp.YoutubeDL(ytdl_options) as ytdlp:
        info = ytdlp.extract_info(yt_query, download=False)
        if "entries" in info:
            return list(info["entries"])
        else:
            return [info]

def get_source(url, output_path):
    ytdl_options = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "0",
        }],
    }

    with yt_dlp.YoutubeDL(ytdl_options) as ytdlp:
        ytdlp.download([url])

def format_artist(ytvideo: YTVideo):
    # TODO: really basic for now improve later please
    title: str = ytvideo.title
    artist_name = ytvideo.uploader

    if "-" in title:
        # artist - track name
        artist_name = title.split("-", 1)[0].strip()

        # TODO: fix "Tyler, The Creator" etc
        # get first artist
        artist_name = artist_name.split(",")[0]

    return artist_name