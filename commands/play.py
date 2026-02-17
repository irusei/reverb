import pymumble_py3.users
import traceback

from handlers.youtube import search_youtube
from main import Reverb
from reverb_types.ytvideo import YTVideo

def run(reverb: Reverb, user: pymumble_py3.users.User, args: list[str]):
    if not reverb.utils.is_in_same_channel(user):
        user.send_text_message("You are not in the same channel!")
        return

    try:
        query = reverb.utils.unhtml_arg(" ".join(args))
        reverb.log.debug("SEARCHING YOUTUBE FOR %s" % query)

        yt_dlp_videos = search_youtube(query)
        reverb.log.debug("FOUND %s VIDEOS" % len(yt_dlp_videos))
        for yt_dlp_video in yt_dlp_videos:
            video = YTVideo(yt_dlp_video)

            reverb.queue.append(video)

            channel: pymumble_py3.mumble.channels.Channel = reverb.mumble.my_channel()
            channel.send_text_message(
                "Added %s to queue [%s] (position %s)" % (video.title, reverb.utils.format_duration(video.duration),
                                                          len(reverb.queue))) # TODO: make it not spam

    except Exception as e:
        user.send_text_message("Something went wrong while executing this command!")
        traceback.print_exception(e)

