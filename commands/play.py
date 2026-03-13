import pymumble_py3.users
import traceback

import utils
from handlers.spotify import parse_spotify
from handlers.youtube import search_youtube_and_add_to_queue
from main import Reverb
from utils import is_spotify

description = "Play a song"
usage = "play <url|query>"
aliases = ['p']

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    try:
        query = utils.unhtml_arg(" ".join(args))

        if is_spotify(query):
            parse_spotify(reverb, query)
            return

        reverb.log.debug("SEARCHING YOUTUBE FOR %s" % query)

        search_youtube_and_add_to_queue(reverb, query)

    except Exception as e:
        user.send_text_message("Something went wrong while executing this command!")
        traceback.print_exception(e)

