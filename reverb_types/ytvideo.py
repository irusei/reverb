class YTVideo:
    def __init__(self, yt_dlp_video: dict):
        self.title = yt_dlp_video.get("title")
        self.url = yt_dlp_video.get("webpage_url") or yt_dlp_video.get("url")
        self.duration = yt_dlp_video.get("duration")
        self.uploader = yt_dlp_video.get("uploader")