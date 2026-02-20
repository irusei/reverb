import pymumble_py3.users

from main import Reverb

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    # skip a number of tracks
    if len(args) > 0:
        if args[0].isdigit():
            number_of_tracks = int(args[0])
            if number_of_tracks > 1:
                for i in range(number_of_tracks):
                    if len(reverb.song_queue) == 0:
                        break

                    reverb.remove_song(reverb.song_queue[0])
                    
    reverb.current_song = None