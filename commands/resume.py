import pymumble_py3.users

from main import Reverb

description = "Resume playback after pause"
usage = "resume"

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    reverb.queue_manager.resume()