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

    if len(reverb.song_queue) < position or position <= 0:
        user.send_text_message("You must provide a valid track position to remove.")
        return

    song = reverb.song_queue[position - 1]

    original_loop = reverb.loop
    reverb.loop = False
    reverb.remove_song(song)
    reverb.loop = original_loop

    if position == 1:
        reverb.current_song = None # skip track

    reverb.mumble.my_channel().send_text_message("Track %s - %s has been removed from the queue." % (song.artist, song.title))