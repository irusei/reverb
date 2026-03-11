from metadata.metadata import Metadata

def format_artist(title, uploader):
    # TODO: really basic for now improve later please
    artist_name = uploader
    if "-" in title:
        # artist - track name
        artist_name = title.split("-", 1)[0].strip()

        # TODO: fix "Tyler, The Creator" etc
        # get first artist
        artist_name = artist_name.split(",")[0]

    return artist_name

class YoutubeSong(Metadata):
    def __init__(self, yt_dlp_results):
        title = yt_dlp_results.get("title")
        url = yt_dlp_results.get("webpage_url") or yt_dlp_results.get("url")
        duration = yt_dlp_results.get("duration")
        uploader = yt_dlp_results.get("uploader")

        super().__init__(title, url, duration, format_artist(title, uploader))