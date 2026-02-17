import pymumble_py3.users

from main import Reverb

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    user.send_text_message("Pong!")
