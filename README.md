# reverb
mumble music bot

## Features

- Play music from YouTube and Spotify*
- Queue management
- Last.fm scrobbling

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

## Notes

- This project is under development
- Last.fm scrobbling requires users to be authenticated and for API keys to be configured in .env
