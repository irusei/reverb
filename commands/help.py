import pymumble_py3

from main import Reverb

description = "Show a list of commands"
usage = "help"

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    commands = "<br>"

    for cmd_name in reverb.commands:
        command_class = reverb.commands[cmd_name]
        commands += reverb.prefix + command_class.usage
        commands += " - "
        commands += command_class.description
        commands += "<br>"

    reverb.mumble.my_channel().send_text_message(commands)