class Song:
    def __init__(self, id, artist, title, duration, url):
        self.id = str(id)
        self.artist = artist
        self.title = title
        self.duration = duration
        self.url = url
        self.source = None
        self.playing = False