import random

from main import Reverb
import pymumble_py3.users

description = "Shuffle the current queue"
usage = "shuffle"


def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    reverb.queue_manager.shuffle_queue()
    reverb.mumble.my_channel().send_text_message("Queue shuffled!")
