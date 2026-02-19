import pymumble_py3.users

from main import Reverb

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.scrobbler.enabled:
        user.send_text_message("last.fm integration is disabled on the bot")
        return

    user.send_text_message(reverb.scrobbler.request_auth_link(user["name"]))
    user.send_text_message("Please run authenticatelastfm once ready.")
