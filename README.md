# reverb
mumble music bot

## Features

- Play music from YouTube and Spotify*
- Queue management
- Last.fm scrobbling
- WebSocket API for externally controlling the queue

*uses YouTube for content
## Setup

### Prerequisites

- uv
- ffmpeg (with opus support)
- a mumble server

### Installation

1. Clone the repository
2. Rename .env.example to .env and configure it

### Running

```bash
uv run main.py
```

## Commands

- `play <query>` - Search YouTube and add songs to queue
- `queue` - Show current queue
- `skip (tracks)` - Skip current song
- `remove (track number)` - Remove track from queue
- `pause/resume` - Pause/resume playback
- `stop` - Clear queue
- `loop` - Toggle loop mode
- `lastfm` - Configure scrobbling with last.fm

## WebSocket API

Connect to the WebSocket server (configured via `SOCKET_HOST`, `SOCKET_PORT`, `SOCKET_AUTH`) to receive real-time updates and control the bot.

### Authentication

Each WebSocket request requires the "auth" field to be set. You can check if the auth is correct by sending
```json
{"type": "verify_auth", "auth": "YOUR_AUTH_KEY"}
```

This will send back `valid auth` or `invalid auth`
The auth is defined by `SOCKET_AUTH` in the .env file

### State Updates

The server broadcasts state updates on queue changes:
```json
{
  "type": "state",
  "value": {
    "paused": false,
    "song_queue": [Song, Song, Song], // these ones have the source field passed, stupid, i know
    "metadata_queue": [Song, Song, Song], // these ones don't and are waiting for the source to be downloaded and processed
    "current_song": Song,
    "loop": false,
    "time": 123.45 // how long the song has been playing for, in seconds
  }
}
```

### Song Object

```json
{
  "id": "uuid",
  "artist": "Artist Name",
  "title": "Song Title",
  "duration": 180,
  "url": "https://...",
  "source": "relative path to mp3 on host, irrelevant"
}
```

## Notes

- This project is under development
- Last.fm scrobbling requires users to be authenticated and for API keys to be configured in .env
- WebSocket server requires `SOCKET_HOST`, `SOCKET_PORT`, and `SOCKET_AUTH` to be configured
