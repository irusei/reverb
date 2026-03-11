from urllib.parse import urlparse

import pymumble_py3.users

def format_duration(duration):
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    return f"{minutes:02d}:{seconds:02d}"


def unhtml_arg(arg):
    if ">" in arg and "<" in arg:
        return arg.split(">")[1].split("<")[0]
    return arg

def is_url(text):
    try:
        result = urlparse(text)
        return result.scheme in ["http", "https"]
    except Exception as e:
        return False

def get_domain_name(url):
    try:
        result = urlparse(url)
        return result.netloc
    except Exception as e:
        return None

def is_youtube(url):
    return is_url(url) and "youtube" in get_domain_name(url)

def is_spotify(url):
    return is_url(url) and "spotify" in get_domain_name(url)


class Utils:
    def __init__(self, reverb):
        self.reverb = reverb

    def is_in_same_channel(self, user: pymumble_py3.users.User):
        return user["channel_id"] == self.reverb.mumble.users.myself["channel_id"]