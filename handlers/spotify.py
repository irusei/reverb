from spotify_scraper import SpotifyClient

from handlers.youtube import search_youtube_and_add_to_queue

client = SpotifyClient()

def get_spotify_type(url):
    if "track" in url:
        return "track"
    elif "playlist" in url:
        return "playlist"
    elif "album" in url:
        return "album"
    else:
        return "unknown"

def parse_spotify(reverb, url):
    tracks = []
    spotify_type = get_spotify_type(url)

    if spotify_type == "track":
        track_info = client.get_track_info(url)
        tracks.append("%s - %s" % (track_info["artists"][0]["name"], track_info["name"]))
    elif spotify_type == "album" or spotify_type == "playlist":
        info = client.get_album_info(url) if spotify_type == "album" else client.get_playlist_info(url)

        for track in info["tracks"]:
            artist_name = track["artists"][0]["name"] if "artists" in track else info["artists"][0]["name"]
            tracks.append("%s - %s" % (artist_name, track["name"]))

    # use ytdl
    for track in tracks:
        search_youtube_and_add_to_queue(reverb, track)