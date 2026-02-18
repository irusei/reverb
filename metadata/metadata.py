import uuid

from filter_rules import clean_title

def format_title(title):
    new_title = title
    if "-" in title:
        new_title = title.split("-", 1)[1]

    # filter rules
    return clean_title(new_title)

class Metadata:
    def __init__(self, title, url, duration, artist):
        self.id = str(uuid.uuid4())
        self.title = format_title(title)
        self.url = url
        self.duration = duration
        self.artist = artist