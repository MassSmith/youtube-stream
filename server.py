# -*- coding: utf-8 -*-
# author: gfw-breaker

import pafy
import requests
from flask import Flask
from flask import Response
from flask import stream_with_context
from flask import render_template
from flask import request

app = Flask(__name__)

video_db = {}
buffer_size = 1024 * 1024  # 1MB
youtube_url = "https://www.youtube.com/watch?v="


class VideoInfo:

    def __init__(self, id, title, url, audio_url, extension, size):
        self.id = id
        self.title = title
        self.url = url
        self.audio_url = audio_url
        self.extension = extension
        self.size = size


def get_video_info(video_id):
    if not video_db.has_key(video_id):
        try:
            video = pafy.new(youtube_url + video_id)
            best = video.getbest()
            audio = video.getbestaudio('m4a')
            video_info = VideoInfo(video_id, video.title, best.url, audio.url, best.extension, best.get_filesize())
            # video_db[video_id] = video_info
            return video_info
        except Exception:
            print 'Error getting video: ' + youtube_url + video_id
            return None
    else:
        return video_db[video_id]


def get_stream(action, video_id, res_type):
    video_info = get_video_info(video_id)

    if res_type == 'video':
        req = requests.get(video_info.url, stream=True, verify=False)
        extension = video_info.extension
    else:
        req = requests.get(video_info.audio_url, stream=True, verify=False)
        extension = 'm4a'

    # file_name = 'filename=' + video_info.title.encode('utf-8') + video_info.extension
    file_name = 'filename=' + video_info.id + '.' + extension
    if action == 'download':
        file_name = 'attachment; ' + file_name

    headers = {
        'Content-Disposition': file_name,
        'Content-Type': 'video/' + extension
    }
    return Response(stream_with_context(req.iter_content(chunk_size=buffer_size)), headers=headers)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/watch')
def watch():
    video_id = request.args.get('v')
    video_info = get_video_info(video_id)
    if video_info is None or video_info.size == 0:
        return render_template("error.html")
    return render_template("watch.html", id=video_info.id, title=video_info.title, extension=video_info.extension)


@app.route('/live')
def play():
    video_id = request.args.get('v')
    return get_stream('live', video_id, 'video')


@app.route('/download')
def download():
    video_id = request.args.get('v')
    res_type = request.args.get('type')
    if res_type == 'audio':
        return get_stream('download', video_id, 'audio')
    else:
        return get_stream('download', video_id, 'video')


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()  # suppress SSL warning
    app.run(host='local_server_ip', port=9999, threaded=True)


# url = "https://www.youtube.com/watch?v=xlj95tyM10c"
# url = "https://www.youtube.com/watch?v=Bey4XXJAqS8"
# url = "https://www.youtube.com/watch?v=92KWubxetbE"
