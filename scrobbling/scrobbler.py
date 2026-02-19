import json
import logging
import os
import threading
import time
import traceback
from json import JSONDecodeError

from scrobbling.lastfmapi import LastFMApi

# TODO: CHECK AUTH OF USER DESPERATELY!!!! THIS IS BAD IF ANOTHER USER CHANGES NICKNAME
class Scrobbler:
    session_store_filename = "sessions.json"
    enabled = False

    def __init__(self, api_key, api_secret):
        self.log = logging.getLogger("scrobbler")
        if api_key is None or api_secret is None:
            self.log.info("last.fm api key not provided, disabling scrobbling functionality")
            return

        self.enabled = True
        self.api = LastFMApi(api_key, api_secret)

        self.unauthenticated_user_tokens = {} # user_name -> (token, time)
        self.session_tokens = self.load_session_tokens()

        incrementing_thread = threading.Thread(target=self.incrementing_thread, daemon=True)
        incrementing_thread.start()

    def load_session_tokens(self):
        if not self.enabled:
            return {}

        self.log.debug("loading session tokens")
        if os.path.exists(self.session_store_filename):
            try:
                with open(self.session_store_filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except JSONDecodeError:
                pass

        return {}

    def save_session_tokens(self):
        if not self.enabled:
            return

        self.log.debug("saving session tokens")
        with open(self.session_store_filename, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in self.session_tokens.items() if v is not None}, f, indent=4)

    def add_session_token(self, user, token):
        if not self.enabled:
            return

        self.log.debug("adding a session token for %s" % user)
        self.session_tokens[user] = token
        self.save_session_tokens()

    def remove_session_token(self, user):
        if not self.enabled:
            return

        self.log.debug("removing session token for %s" % user)
        self.session_tokens.pop(user, None)
        self.save_session_tokens()

    # increment timer
    def incrementing_thread(self):
        while True:
            for user in self.unauthenticated_user_tokens:
                token, time_elapsed = self.unauthenticated_user_tokens[user]
                self.unauthenticated_user_tokens[user] = (token, time_elapsed + 1)

            time.sleep(1)

    def get_user_token(self, user):
        if not self.enabled:
            return None

        self.log.debug("getting user token for %s" % user)
        if user in self.unauthenticated_user_tokens:
            token, time_elapsed = self.unauthenticated_user_tokens[user]

            if time_elapsed < 2000: # i don't know after how long it expires so let's say 2000 seconds
                return token

        token = self.api.get_token()
        self.unauthenticated_user_tokens[user] = (token, 0)
        return token

    def request_auth_link(self, user):
        if not self.enabled:
            return None

        token = self.get_user_token(user)
        return self.api.get_auth_url(token)

    def is_authenticated(self, user):
        if not self.enabled:
            return False

        return user in self.session_tokens and self.session_tokens[user] is not None

    def get_session_key(self, user):
        if not self.enabled:
            return None

        if user in self.session_tokens:
            return self.session_tokens[user]["session"]["key"]
        else:
            return None

    def finish_authenticating(self, user):
        if not self.enabled:
            return

        self.log.debug("attempting to authenticate %s" % user)
        # this code will only work if user authenticated but we have no way of checking that
        try:
            session_token = self.api.get_session_token(self.get_user_token(user)) # This could error if user is slow enough
            if "error" in session_token:
                return

            self.add_session_token(user, session_token)


        except Exception as e:
            traceback.print_exception(e)

    def deauth(self, user):
        if not self.enabled:
            return

        self.remove_session_token(user)

    def update_now_playing(self, user, artist, track, duration):
        if not self.enabled:
            return

        self.log.debug("updating now playing for %s: %s - %s" % (user, artist, track))
        try:
            if self.is_authenticated(user):
                self.api.update_now_playing(self.get_session_key(user), artist, track, duration)
        except Exception as e:
            traceback.print_exception(e)

    def scrobble_track(self, user, artist, track, timestamp):
        if not self.enabled:
            return

        self.log.debug("scrobbling for %s: %s - %s" % (user, artist, track))
        try:
            if self.is_authenticated(user):
                self.api.scrobble_track(self.get_session_key(user), artist, track, timestamp)
        except Exception as e:
            traceback.print_exception(e)



