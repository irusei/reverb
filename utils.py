import html
import math

import pymumble_py3.users

class Utils:
    def __init__(self, reverb):
        self.reverb = reverb

    def is_in_same_channel(self, user: pymumble_py3.users.User):
        return user["channel_id"] == self.reverb.mumble.users.myself["channel_id"]

    def format_duration(self, duration):
        minutes = math.floor(duration / 60)
        seconds = math.ceil(duration % 60)

        return "%s:%s" % (minutes, seconds)

    def unhtml_arg(self, arg):
        # TODO: make this better
        arg = html.unescape(arg)
        if ">" not in arg:
            return arg
        return arg.split(">")[1].split("<")[0]