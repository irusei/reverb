import pymumble_py3.users

from main import Reverb

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    reverb.metadata_queue.clear()
    reverb.song_queue.clear()
    reverb.current_song = None

    reverb.mumble.my_channel().send_text_message("The queue has been cleared.")