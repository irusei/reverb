import hashlib

import requests

LAST_FM_API_HOME = "https://ws.audioscrobbler.com/2.0/"
class LastFMApi:
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def get_api_sig(self, parameters):
        api_sig = ""

        for key, value in sorted(parameters.items()):
            if key == "format":
                continue

            api_sig += key
            api_sig += str(value)

        api_sig += self.secret
        return hashlib.md5(api_sig.encode("utf-8")).hexdigest()

    def get_token(self):
        request = requests.get(LAST_FM_API_HOME + "?method=auth.getToken&api_key=%s&format=json" % self.key)
        json = request.json()
        return json["token"]

    def get_session_token(self, token):
        parameters = {
            "api_key": self.key,
            "method": "auth.getSession",
            "token": token,
            "format": "json"
        }

        api_sig = self.get_api_sig(parameters)
        parameters["api_sig"] = api_sig

        request = requests.post(LAST_FM_API_HOME, data=parameters)
        json = request.json()

        return json

    def get_auth_url(self, token):
        return "https://www.last.fm/api/auth/?api_key=%s&token=%s" % (self.key, token)

    def update_now_playing(self, session_key, artist, track, duration):
        parameters = {
            "api_key": self.key,
            "method": "track.updateNowPlaying",
            "artist": artist,
            "track": track,
            "duration": duration,
            "sk": session_key
        }

        api_sig = self.get_api_sig(parameters)
        parameters["api_sig"] = api_sig

        requests.post(LAST_FM_API_HOME, data=parameters)

    def scrobble_track(self, session_key, artist, track, timestamp):
        parameters = {
            "api_key": self.key,
            "method": "track.scrobble",
            "artist": artist,
            "track": track,
            "timestamp": timestamp,
            "sk": session_key
        }

        api_sig = self.get_api_sig(parameters)
        parameters["api_sig"] = api_sig

        requests.post(LAST_FM_API_HOME, data=parameters)