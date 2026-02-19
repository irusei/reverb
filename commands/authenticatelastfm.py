import pymumble_py3.users

from main import Reverb

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.scrobbler.enabled:
        user.send_text_message("last.fm integration is disabled on the bot")
        return

    reverb.scrobbler.finish_authenticating(user["name"])

    if reverb.scrobbler.is_authenticated(user["name"]):
        user.send_text_message("Succesfully connected to last.fm!")
    else:
        user.send_text_message("Something went wrong, try connecting again.")