class YTVideo:
    def __init__(self, yt_dlp_video: dict):
        self.title = yt_dlp_video.get("title")
        self.url = yt_dlp_video.get("webpage_url")
        self.duration = yt_dlp_video.get("duration")
        self.uploader = yt_dlp_video.get("uploader")
        self.views = yt_dlp_video.get("view_count")
        self.thumbnail = yt_dlp_video.get("thumbnail")