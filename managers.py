import subprocess as sp
import uuid
from time import sleep, time

from yt_dlp import DownloadError

import handlers.youtube as youtube
import utils


class QueueManager:
    def __init__(self, reverb):
        self.reverb = reverb
        self.log = reverb.log

    def skip_track(self, remove_from_loop=False):
        if self.reverb.current_song:
            self.remove_song(self.reverb.current_song, remove_from_loop=remove_from_loop)
            self.reverb.current_song = None

    def set_loop(self, loop):
        self.reverb.loop = loop
        status = "enabled" if loop else "disabled"
        channel = self.reverb.mumble.my_channel()
        channel.send_text_message(f"Loop {status}")

    def toggle_loop(self):
        self.set_loop(not self.reverb.loop)

    def pause(self):
        self.reverb.paused = True

    def resume(self):
        self.reverb.paused = False

    def toggle_pause(self):
        if self.reverb.paused:
            self.resume()
        else:
            self.pause()

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
                song_start_time = time()

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
                    "Now playing: %s - %s [%s]" % (next_song.artist, next_song.title, utils.format_duration(next_song.duration)))

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
                                if self.reverb.channel_join_times[user_name] <= song_start_time:
                                    if self.reverb.scrobbler.is_authenticated(user_name):
                                        self.reverb.scrobbler.scrobble_track(user_name, next_song.artist, next_song.title,
                                                                          int(time()) - scrobble_timer)

                    sleep(0.01)

                self.reverb.current_song = None
                self.remove_song(next_song)


class ConverterManager:
    def __init__(self, reverb):
        self.reverb = reverb
        self.log = reverb.log

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

                unqueued_song.id = str(uuid.uuid4())
                source = "./cache/%s" % unqueued_song.id

                try:
                    youtube.get_source(unqueued_song.url, source)
                except DownloadError as e:
                    self.reverb.metadata_queue.remove(unqueued_song)
                    channel = self.reverb.mumble.my_channel()
                    channel.send_text_message(
                        f"Failed to download {unqueued_song.artist} - {unqueued_song.title}: {str(e)}")
                    continue

                source += ".mp3"
                unqueued_song.source = source

                self.reverb.song_queue.append(unqueued_song)
                new_songs.add(unqueued_song)

            if len(new_songs) > 0:
                channel = self.reverb.mumble.my_channel()
                queue_diff = "Added:"

                for idx, song in enumerate(self.reverb.song_queue):
                    if song in new_songs:
                        queue_diff += f"<br>{song.artist} - {song.title} [{utils.format_duration(song.duration)}] (position {idx + 1})"

                channel.send_text_message(queue_diff[:512])
