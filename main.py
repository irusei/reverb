import os
import threading
import ctypes.util
import signal
from time import time

from dotenv import load_dotenv

if "OPUS_LIBRARY" in os.environ:
    ctypes.util.find_library = lambda name: (
        os.environ["OPUS_LIBRARY"] if name == "opus"
        else ctypes.util.find_library(name)
    )

import pymumble_py3 as pymumble
import logging

import pymumble_py3.constants
from pymumble_py3.messages import TextMessage

import certificate
from reverb_types.song import Song
from managers import QueueManager, ConverterManager
from scrobbling.scrobbler import Scrobbler

load_dotenv()
PREFIX = os.getenv('PREFIX')
SERVER = os.getenv('SERVER')
PORT = int(os.getenv('PORT'))
PASSWORD = os.getenv('PASSWORD')
USER_NAME = os.getenv('USER_NAME')

LAST_FM_API_KEY = os.getenv('LAST_FM_API_KEY') or None
LAST_FM_API_SECRET = os.getenv('LAST_FM_API_SECRET') or None

def prepare_folders():
    os.makedirs("./cache", exist_ok=True)

class Reverb:
    def __init__(self, mumble: pymumble.Mumble):
        self.log = logging.getLogger("bot")
        logging.basicConfig(level=logging.DEBUG)
        self.log.setLevel(logging.DEBUG)
        self.utils = Utils(self)
        self.mumble: pymumble.Mumble = mumble
        self.metadata_queue: list[Song] = []
        self.song_queue: list[Song] = []
        self.current_song = None
        self.channel_join_times: dict[str, float] = {}  # user_name -> channel join timestamp
        self.commands: dict[str, Command] = dict()
        self.paused = False
        self.volume = -25
        self.loop = False
        self.scrobbler = Scrobbler(LAST_FM_API_KEY, LAST_FM_API_SECRET)
        self.queue_manager = QueueManager(self)
        self.converter_manager = ConverterManager(self)
        self.mumble.start()
        self.mumble.is_ready()

        mumble.set_bandwidth(192000)

        prepare_folders()
        self.clear_cache(full=True)
        self.register_commands()
        # callbacks
        self.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
                                           self.message_received)
        self.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_USERUPDATED,
                                           self.user_updated)
        self.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_USERCREATED,
                                           self.user_updated)

        # run user_updated for each user present in channel
        my_channel: pymumble_py3.mumble.channels.Channel = mumble.my_channel()
        for user in my_channel.get_users():
            self.user_updated(user)

        worker_thread = threading.Thread(target=self.queue_manager.worker_thread, daemon=True)
        worker_thread.start()

        converter_thread = threading.Thread(target=self.converter_manager.run, daemon=True)
        converter_thread.start()

    def register_commands(self):
        folder = "./commands"

        for file in os.listdir(folder):
            if file.endswith(".py"):
                command_name = file.split(".")[0]  # remove the extension
                self.commands[command_name] = Command(command_name)
                self.log.debug(f"registered command {command_name}")

    def handle_command(self, user: pymumble.mumble.users.User, command: str, args: list[str]):
        # check if command exists
        if command in self.commands:
            cmd_class = self.commands[command]
            command_thread = threading.Thread(target=cmd_class.run, args=(self, user, args), daemon=True)
            command_thread.start()
            self.log.debug(f"command ran from {user['name']}: {command} {' '.join(args)}")

    def message_received(self, text: TextMessage):
        user: pymumble.mumble.users.User = self.mumble.users[text.actor]

        if user is self.mumble.users.myself:
            return

        self.log.debug(f"message received from {user['name']}: {text.message}")

        message: str = text.message.strip()
        # check if is command
        if message.startswith(PREFIX):
            args = message.split(" ")
            command = args[0]
            args.remove(command)
            command = command[1:]  # remove prefix
            # handle command
            self.handle_command(user, command, args)

    def user_updated(self, user_state: dict, modified_fields: dict = None):
        user_name = user_state.get("name")
        if user_name:
            self.channel_join_times[user_name] = time()

    def clear_cache(self, full=False):
        for file_name in os.listdir("./cache"):
            no_extension = os.path.splitext(file_name)[0]
            in_queue = any(metadata.id == no_extension.strip() for metadata in self.metadata_queue)

            if not full:
                if not in_queue and no_extension != file_name:  # avoid yt-dlp temp files
                    os.remove(os.path.join("./cache", file_name))
            else:
                os.remove(os.path.join("./cache", file_name))


if __name__ == "__main__":
    from reverb_types.command import Command
    from utils import Utils

    if not os.path.exists("./cert.pem"):
        certificate.gen_certificate()

    Reverb(pymumble.Mumble(SERVER, USER_NAME, PORT, PASSWORD, reconnect=True, certfile="./cert.pem"))

    signal.pause()
