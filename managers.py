import asyncio
import json
import socket
import subprocess as sp
import uuid
import threading
from json import JSONDecodeError
from time import sleep, time

import websockets
from yt_dlp import DownloadError

import handlers.youtube as youtube
import utils
from handlers.spotify import parse_spotify
from handlers.youtube import search_youtube_and_add_to_queue
from utils import is_spotify


class QueueManager:
    def __init__(self, reverb):
        self.song_start_time = None
        self.reverb = reverb
        self.log = reverb.log

    def skip_track(self, remove_from_loop=False):
        if self.reverb.current_song:
            self.remove_song(self.reverb.current_song, remove_from_loop=remove_from_loop)
            self.reverb.current_song = None

        if self.reverb.socket_manager is not None:
            self.reverb.socket_manager.announce()

    def set_loop(self, loop):
        self.reverb.loop = loop
        status = "enabled" if loop else "disabled"
        channel = self.reverb.mumble.my_channel()
        channel.send_text_message(f"Loop {status}")

    def toggle_loop(self):
        self.set_loop(not self.reverb.loop)
        if self.reverb.socket_manager is not None:
            self.reverb.socket_manager.announce()

    def pause(self):
        self.reverb.paused = True

    def resume(self):
        self.reverb.paused = False

    def toggle_pause(self):
        if self.reverb.paused:
            self.resume()
        else:
            self.pause()

        if self.reverb.socket_manager is not None:
            self.reverb.socket_manager.announce()

    def get_queue(self):
        return self.reverb.song_queue.copy()

    def get_metadata_queue(self):
        return self.reverb.metadata_queue.copy()

    def get_current_song(self):
        return self.reverb.current_song

    def get_queue_size(self):
        return len(self.reverb.song_queue)

    def remove_song(self, song, remove_from_loop=False):
        for metadata in self.reverb.metadata_queue.copy():
            if metadata.id == song.id:
                self.reverb.metadata_queue.remove(metadata)
                if self.reverb.loop and not remove_from_loop:
                    self.reverb.metadata_queue.append(metadata)
                break

        if song in self.reverb.song_queue:
            self.reverb.song_queue.remove(song)
            if self.reverb.loop and not remove_from_loop:
                self.reverb.song_queue.append(song)

        if self.reverb.socket_manager is not None:
            self.reverb.socket_manager.announce()

    def add_to_metadata_queue(self, song):
        id_set = set(s.id for s in self.reverb.song_queue)
        if song.id in id_set:
            return False
        self.reverb.metadata_queue.append(song)
        return True

    def clear_queue(self):
        self.reverb.metadata_queue.clear()
        self.reverb.song_queue.clear()
        self.reverb.current_song = None

    def shuffle_queue(self):
        import random
        random.shuffle(self.reverb.song_queue)
        if self.reverb.socket_manager is not None:
            self.reverb.socket_manager.announce()

    def worker_thread(self):
        while True:
            if self.reverb.current_song is None:
                if len(self.reverb.song_queue) == 0:
                    sleep(0.01)
                    continue

                self.reverb.clear_cache()
                next_song = self.reverb.song_queue[0]

                if next_song is None:
                    continue

                self.reverb.current_song = next_song
                self.song_start_time = time()

                command = [
                    "ffmpeg",
                    "-i", next_song.source,
                    "-f", "s16le",
                    "-ac", "1",
                    "-ar", "48000",
                    "-af", "aresample=resampler=soxr,volume=%sdB" % str(self.reverb.volume),
                    "-"
                ]

                channel = self.reverb.mumble.my_channel()
                channel.send_text_message(
                    "<br><b>Now Playing</b><br><font size=\"5\" color=\"#4CAF50\">%s - %s</font><br><i>[%s]</i>" % (next_song.artist, next_song.title, utils.format_duration(next_song.duration)))

                sound = sp.Popen(command, stdout=sp.PIPE, stderr=sp.DEVNULL, bufsize=1024)
                while True:
                    raw_music = sound.stdout.read(1024)
                    if not raw_music:
                        sound.kill()
                        break

                    self.reverb.mumble.sound_output.add_sound(raw_music)

                # last.fm things
                scrobble_timer = min(240, next_song.duration / 2)
                scrobble_time = int(time()) + scrobble_timer
                should_scrobble = self.reverb.scrobbler.enabled and next_song.duration > 30

                # update last.fm now playing
                if should_scrobble:
                    for user in channel.get_users():
                        user_name = user["name"]
                        if self.reverb.scrobbler.is_authenticated(user_name):
                            self.reverb.scrobbler.update_now_playing(user_name, next_song.artist, next_song.title, next_song.duration)

                if self.reverb.socket_manager is not None:
                    self.reverb.socket_manager.announce()

                pause_buffer = None
                while pause_buffer is not None or self.reverb.mumble.sound_output.get_buffer_size() > 0.5:
                    if self.reverb.paused and pause_buffer is None:
                        pause_buffer = self.reverb.mumble.sound_output.pcm
                        self.reverb.mumble.sound_output.clear_buffer()
                        sleep(0.01)
                        continue

                    if not self.reverb.paused and pause_buffer is not None:
                        self.reverb.mumble.sound_output.pcm = pause_buffer
                        pause_buffer = None

                    if self.reverb.current_song is None:
                        self.reverb.paused = False
                        self.reverb.mumble.sound_output.clear_buffer()
                        sound.kill()
                        break

                    # scrobble track
                    # check if track should be scrobbled
                    if should_scrobble and int(time()) >= scrobble_time:
                        should_scrobble = False # so it doesn't scrobble again
                        for user in channel.get_users():
                            user_name = user["name"]
                            # only scrobble for users who were in the channel when song started
                            if user_name in self.reverb.channel_join_times:
                                if self.reverb.channel_join_times[user_name] <= self.song_start_time:
                                    if self.reverb.scrobbler.is_authenticated(user_name):
                                        self.reverb.scrobbler.scrobble_track(user_name, next_song.artist, next_song.title,
                                                                          int(time()) - scrobble_timer)

                    sleep(0.01)

                self.reverb.current_song = None
                self.song_start_time = None
                self.remove_song(next_song)

class SocketManager:
    def __init__(self, reverb, host, port, auth_key):
        self.reverb = reverb
        self.log = reverb.log
        self.sockets = []

        self.host = host
        self.port = port
        self.auth_key = auth_key

    async def _announce_async(self):
        for ws in self.sockets:
            await ws.send(self.get_state())

    def get_state(self):
        return json.dumps({
            "type": "state",
            "value": {
                "paused": self.reverb.paused,
                "song_queue": [song.to_dict() for song in self.reverb.song_queue],
                "metadata_queue": [metadata.to_dict() for metadata in self.reverb.metadata_queue],
                "current_song": self.reverb.current_song.to_dict() if self.reverb.current_song is not None else None,
                "loop": self.reverb.loop,
                "time": time() - self.reverb.queue_manager.song_start_time if self.reverb.queue_manager.song_start_time is not None else None
            }
        })

    async def handler(self, websocket):
        sent_initial = False
        self.sockets.append(websocket)
        async for message in websocket:
            try:
                data_json: dict = json.loads(message)

                command_type = data_json.get("type", None)
                auth = data_json.get("auth", None)
                args = data_json.get("args", None)

                if auth != self.auth_key:
                    await websocket.send("invalid auth")
                    continue

                if not command_type:
                    await websocket.send("invalid parameters")
                    continue

                if command_type == "verify_auth":
                    await websocket.send("valid auth")

                elif command_type == "play_song":
                    search_youtube_and_add_to_queue(self.reverb, args)

                elif command_type == "skip_song":
                    self.reverb.queue_manager.skip_track()

                elif command_type == "remove_song":
                    try:
                        index = int(args)
                        if self.reverb.queue_manager.get_queue_size() >= index >= 0:
                            song = self.reverb.song_queue[index]
                            self.reverb.queue_manager.remove_song(song)

                            if index == 0:
                                self.reverb.queue_manager.skip_track()
                    except Exception:
                        pass

                elif command_type in ["pause_song", "resume_song"]:
                    self.reverb.queue_manager.toggle_pause()

                elif command_type == "toggle_loop":
                    self.reverb.queue_manager.toggle_loop()

                elif command_type == "receive" and not sent_initial:
                    sent_initial = True
                    await websocket.send(self.get_state())

                elif command_type == "get_time":
                    if self.reverb.current_song is not None:
                        await websocket.send(json.dumps({
                            "type": "time",
                            "value": time() - self.reverb.queue_manager.song_start_time if self.reverb.queue_manager.song_start_time is not None else None
                        }))

            except JSONDecodeError:
                continue
        self.sockets.remove(websocket)

    async def _run_async(self):
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever

    def run(self):
        asyncio.run(self._run_async())

    def announce(self):
        try:
            try:
                asyncio.create_task(self._announce_async())
            except:
                asyncio.run(self._announce_async())
        except:
            pass

class ConverterManager:
    def __init__(self, reverb):
        self.reverb = reverb
        self.log = reverb.log

    def _download_song(self, unqueued_song):
        unqueued_song.id = str(uuid.uuid4())
        source = "./cache/%s" % unqueued_song.id

        try:
            youtube.get_source(unqueued_song.url, source)
        except DownloadError as e:
            self.reverb.metadata_queue.remove(unqueued_song)
            channel = self.reverb.mumble.my_channel()
            channel.send_text_message(
                f"Failed to download {unqueued_song.artist} - {unqueued_song.title}: {str(e)}")
            return

        source += ".flac"
        unqueued_song.source = source

        self.reverb.song_queue.append(unqueued_song)

    def run(self):
        while True:
            if len(self.reverb.metadata_queue) == 0:
                sleep(0.01)
                continue

            id_set = set(song.id for song in self.reverb.song_queue)
            new_songs = set()

            for unqueued_song in self.reverb.metadata_queue.copy():
                if unqueued_song.id in id_set:
                    sleep(0.01)
                    continue

                if unqueued_song.url is None:
                    self.reverb.metadata_queue.remove(unqueued_song)
                    continue

                self._download_song(unqueued_song)
                new_songs.add(unqueued_song)


            if len(new_songs) > 0:
                channel = self.reverb.mumble.my_channel()
                queue_diff = "Added:"

                for idx, song in enumerate(self.reverb.song_queue):
                    if song in new_songs:
                        queue_diff += f"<br>{song.artist} - {song.title} [{utils.format_duration(song.duration)}] (position {idx + 1})"

                channel.send_text_message(queue_diff[:512])
                if self.reverb.socket_manager is not None:
                    self.reverb.socket_manager.announce()
