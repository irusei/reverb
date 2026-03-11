import re

from reverb_types.song import Song
from filter_rules import clean_title

def format_artist(title, uploader):
    # TODO: really basic for now improve later please
    artist_name = uploader
    if "-" in title:
        # artist - track name
        artist_name = title.split("-", 1)[0].strip()

        # TODO: fix "Tyler, The Creator, Childish Gambino" etc
        # get first artist
        artist_name = artist_name.split(",")[0]

    return artist_name

class YoutubeSong(Song):
    def __init__(self, yt_dlp_results):
        title = yt_dlp_results.get("title")
        url = yt_dlp_results.get("webpage_url") or yt_dlp_results.get("url")
        duration = yt_dlp_results.get("duration")
        uploader = yt_dlp_results.get("uploader")

        super().__init__(
            id=None,  # will be set when added to queue
            artist=format_artist(title, uploader),
            title=format_title(title),
            duration=duration,
            url=url
        )

def format_title(title):
    new_title = title.replace("—","-")
    if "-" in new_title:
        new_title = new_title.split("-", 1)[1]
    return clean_title(new_title)