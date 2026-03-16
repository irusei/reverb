class Song:
    def __init__(self, id, artist, title, duration, url):
        self.id = str(id)
        self.artist = artist
        self.title = title
        self.duration = duration
        self.url = url
        self.source = None

    def to_dict(self):
        return {
            "id": self.id,
            "artist": self.artist,
            "title": self.title,
            "duration": self.duration,
            "url": self.url,
            "source": self.source
        }