import pymumble_py3.users

from main import Reverb

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    reverb.loop = not reverb.loop

    channel: pymumble_py3.mumble.channels.Channel = reverb.mumble.my_channel()
    channel.send_text_message("Queue loop set to: %s" % ("on" if reverb.loop else "off"))