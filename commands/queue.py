import pymumble_py3.users
import utils
from main import Reverb


def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    queue_response = ""

    # inform user if songs are being processed
    if len(reverb.song_queue) != len(reverb.metadata_queue):
        queue_response += "Songs are currently being processed, queue might take a moment to catch up"

    for index in range(len(reverb.song_queue)):
        song = reverb.song_queue[index]

        queue_response += "<br>%s. %s - %s [%s]" % (index + 1, song.artist, song.title, utils.format_duration(song.duration))

    channel = reverb.mumble.my_channel()
    if queue_response != "":
        channel.send_text_message(queue_response[:512])
    else:
        channel.send_text_message("No songs in queue!")
