import pymumble_py3.users

from main import Reverb

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.scrobbler.enabled:
        user.send_text_message("last.fm integration is disabled on the bot")
        return

    command = args[0] if len(args) > 0 else None
    if command == "connect":
        user.send_text_message(reverb.scrobbler.request_auth_link(user["name"]))
        user.send_text_message("Please run \"lastfm done\" once ready.")
    elif command == "done":
        reverb.scrobbler.finish_authenticating(user["name"])

        if reverb.scrobbler.is_authenticated(user["name"]):
            user.send_text_message("Succesfully connected to last.fm!")
        else:
            user.send_text_message("Something went wrong, try connecting again.")
    elif command == "disconnect":
        if reverb.scrobbler.is_authenticated(user["name"]):
            reverb.scrobbler.deauth(user["name"])
        else:
            user.send_text_message("You're not connected to last.fm!")
            return

        if not reverb.scrobbler.is_authenticated(user["name"]):
            user.send_text_message("Succesfully disconnected last.fm :(")
        else:
            user.send_text_message("Something went wrong, try disconnecting again.")
    else:
        user.send_text_message("lastfm [connect/disconnect/done]")