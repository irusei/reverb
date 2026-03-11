import pymumble_py3.users
from main import Reverb

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    if len(args) == 0 or not args[0].isdigit():
        user.send_text_message("You must provide a valid track position to remove.")
        return

    position = int(args[0])

    if reverb.queue_manager.get_queue_size() < position or position <= 0:
        user.send_text_message("You must provide a valid track position to remove.")
        return

    # skip song at position
    song = reverb.metadata_queue[position - 1]
    reverb.queue_manager.remove_song(song, remove_from_loop=True)

    if position == 1:
        reverb.queue_manager.skip_track()

    reverb.mumble.my_channel().send_text_message("Track %s - %s has been removed from the queue." % (song.artist, song.title))
