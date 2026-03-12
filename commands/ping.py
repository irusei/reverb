import pymumble_py3.users

from main import Reverb

description = "Check if the bot is responding"
usage = "ping"

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    user.send_text_message("Pong!")
