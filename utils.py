import html
import math
from urllib.parse import urlparse

import pymumble_py3.users

def format_duration(duration):
    minutes: str = str(math.floor(duration / 60))
    seconds: str = str(math.ceil(duration % 60))

    return "%s:%s" % (minutes.zfill(2), seconds.zfill(2))


def unhtml_arg(arg):
    # TODO: make this better
    arg = html.unescape(arg)
    if ">" not in arg:
        return arg
    return arg.split(">")[1].split("<")[0]

def is_url(text):
    try:
        result = urlparse(text)
        return result.scheme in ["http", "https"]
    except Exception as e:
        return False

class Utils:
    def __init__(self, reverb):
        self.reverb = reverb

    def is_in_same_channel(self, user: pymumble_py3.users.User):
        return user["channel_id"] == self.reverb.mumble.users.myself["channel_id"]