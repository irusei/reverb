import yt_dlp

def search_youtube(query, limit=1):
    ytdl_options = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True
    }

    yt_query = f"ytsearch{limit}:{query}"
    if "https://" in query or "http://" in query:
        yt_query = query

    if "list=" in query or "/sets/" in query:
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
