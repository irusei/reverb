import subprocess as sp
import os
import threading
import uuid
from time import sleep

from dotenv import load_dotenv
import pymumble_py3 as pymumble
import logging

import pymumble_py3.constants
from pymumble_py3.messages import TextMessage

from reverb_types.song import Song
from reverb_types.ytvideo import YTVideo

import handlers.youtube as youtube

load_dotenv()
PREFIX = os.getenv('PREFIX')
SERVER = os.getenv('SERVER')
PORT = int(os.getenv('PORT'))
PASSWORD = os.getenv('PASSWORD')
USER_NAME = os.getenv('USER_NAME')


def prepare_folders():
    os.makedirs("./cache", exist_ok=True)

class Reverb:
    def __init__(self, mumble: pymumble.Mumble):
        self.log = logging.getLogger("bot")
        logging.basicConfig(level=logging.DEBUG)
        self.log.setLevel(logging.DEBUG)
        self.utils = Utils(self)
        self.mumble: pymumble.Mumble = mumble
        self.queue = []
        self.song_queue: list[Song] = []
        self.current_song = None
        self.commands: dict[str, Command] = dict()
        self.paused = False

        self.mumble.start()
        self.mumble.is_ready()

        mumble.set_bandwidth(192000)

        prepare_folders()
        self.register_commands()
        # callbacks
        self.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_TEXTMESSAGERECEIVED,
                                           self.message_received)

        worker_thread = threading.Thread(target=self.worker_thread, daemon=True)
        worker_thread.start()

        converter_thread = threading.Thread(target=self.converter_thread, daemon=True)
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
        self.log.debug(f"message received from {user['name']}: {text.message}")

        message: str = text.message
        # check if is command
        if message.startswith(PREFIX):
            args = message.split(" ")
            command = args[0]
            args.remove(command)
            command = command[1:]  # remove prefix
            # handle command
            self.handle_command(user, command, args)

    def clear_cache(self):
        for file_name in os.listdir("./cache"):
            no_extension = os.path.splitext(file_name)[0]
            in_queue = any(str(queued.id) == no_extension.strip() for queued in self.song_queue)

            if not in_queue and no_extension != file_name: # avoid yt-dlp temp files
                os.remove(os.path.join("./cache", file_name))


    def converter_thread(self):
        while True:
            if len(self.queue) == 0:
                sleep(0.01)
                continue

            counterparts = set(song.counterpart for song in self.song_queue)

            for unqueued_song in self.queue.copy():
                if unqueued_song in counterparts:
                    sleep(0.01)
                    continue

                # Convert to "Song" class
                if isinstance(unqueued_song, YTVideo):
                    if unqueued_song.url is None:
                        self.queue.remove(unqueued_song)
                        continue

                    id = uuid.uuid4()
                    source = "./cache/%s" % id
                    youtube.get_source(unqueued_song.url, source)
                    source += ".mp3"  # yt-dlp appends .mp3 for some reason
                    song = Song(id, youtube.format_artist(unqueued_song), self.utils.format_title(unqueued_song.title), unqueued_song.duration, source)
                    song.counterpart = unqueued_song

                    self.song_queue.append(song)

    def remove_song(self, song: Song):
        self.queue.remove(song.counterpart)
        self.song_queue.remove(song)

    def worker_thread(self):
        while True:
            if self.current_song is None:
                if len(self.song_queue) == 0:
                    sleep(0.01)
                    continue

                # clear cache
                self.clear_cache()

                next_song = self.song_queue[0]

                if next_song is None:
                    continue

                self.current_song = next_song

                # play song
                command = [
                    "ffmpeg",
                    "-i", next_song.source,
                    "-f", "s16le",
                    "-ac", "1",
                    "-ar", "48000",
                    "-"
                ]

                # broadcast playing
                channel: pymumble_py3.mumble.channels.Channel = self.mumble.my_channel()
                channel.send_text_message(
                    "Now playing: %s - %s [%s]" % (next_song.artist, next_song.title, self.utils.format_duration(next_song.duration)))
                sound = sp.Popen(command, stdout=sp.PIPE, stderr=sp.DEVNULL, bufsize=1024)
                while True:
                    raw_music = sound.stdout.read(1024)
                    if not raw_music:
                        sound.kill()
                        break

                    self.mumble.sound_output.add_sound(raw_music)

                pause_buffer = None
                while pause_buffer is not None or self.mumble.sound_output.get_buffer_size() > 0.5:
                    if self.paused and pause_buffer is None:
                        pause_buffer = self.mumble.sound_output.pcm
                        self.mumble.sound_output.clear_buffer()
                        sleep(0.01)
                        continue

                    if not self.paused and pause_buffer is not None:
                        self.mumble.sound_output.pcm = pause_buffer
                        pause_buffer = None

                    if self.current_song is None:
                        self.paused = False # resume song
                        self.mumble.sound_output.clear_buffer()
                        sound.kill()
                        break

                    sleep(0.01)

                self.current_song = None
                self.remove_song(next_song)


if __name__ == "__main__":
    from reverb_types.command import Command
    from utils import Utils

    Reverb(pymumble.Mumble(SERVER, USER_NAME, PORT, PASSWORD, reconnect=True))

    input()
