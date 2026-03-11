class Song:
    def __init__(self, id, artist, title, duration, source):
        self.artist = artist
        self.title = title
        self.duration = duration
        self.source = source
        self.id = str(id)
        self.playing = False