# -*- coding: utf-8 -*-
# author: gfw-breaker
import re

import pafy
import requests
import lru
import urllib
from flask import Flask
from flask import Response
from flask import stream_with_context
from flask import render_template
from flask import request

app = Flask(__name__)
cache = lru.LRUCacheDict(max_size=100, expiration=60*60, concurrent=True)

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
    if not cache.has_key(video_id):
        try:
            video = pafy.new(youtube_url + video_id)
            best = video.getbest('mp4')
            audio = video.getbestaudio('m4a')
            video_info = VideoInfo(video_id, video.title, best.url, audio.url, best.extension, best.get_filesize())
            cache[video_id] = video_info
            return video_info
        except Exception as e:
            print e.message
            print 'failed to get video: ' + youtube_url + video_id
            return None
    else:
        print 'getting cached video info: ' + video_id
        return cache[video_id]


def get_stream(action, video_id, res_type, r_start, r_end=None):
    video_info = get_video_info(video_id)
    file_size = video_info.size

    start = r_start
    if r_end is None:
        r_end = file_size - 1
    length = min(r_end - start + 1, 1024*1024*10)
    end = start + length - 1
    print end

    url = '{0}&range={1}-{2}'.format(video_info.url, start, end)
    #print url
    hhds = { 'Range': 'bytes={0}-{1}'.format(start, end) }
    #req = requests.get(video_info.url, stream=True, verify=False, headers=hhds)
    req = requests.get(video_info.url, verify=False, headers=hhds)
    length = len(req.content)
    #print length
    #print req.headers
    extension = video_info.extension

    headers = {
        'Content-Type': 'video/' + extension,
        'Content-Length': length,
        'Accept-Ranges': 'bytes',
        'Content-Range': 'bytes {0}-{1}/{2}'.format(start, end, file_size)
    }
    return Response(req.content, 206, headers=headers)


def dl_stream(action, video_id, res_type):
    video_info = get_video_info(video_id)

    if res_type == 'video':
        req = requests.get(video_info.url, stream=True, verify=False)
        extension = video_info.extension
    else:
        req = requests.get(video_info.audio_url, stream=True, verify=False)
        extension = 'm4a'

    # file_name = 'filename=' + video_info.id + '.' + extension
    file_name = 'filename=' + urllib.quote(video_info.title.encode('utf-8')) + '.' + extension
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
    video_id = request.args.get('v').split('.')[0]
    video_info = get_video_info(video_id)
    if video_info is None or video_info.size == 0:
        return render_template("error.html")
    return render_template("watch.html", id=video_info.id, title=video_info.title, extension=video_info.extension)


@app.route('/embed/<video_id>')
def embed(video_id):
    video_info = get_video_info(video_id)
    return render_template("embed.html", id=video_info.id, title=video_info.title, extension=video_info.extension)


@app.route('/live')
def play():
    video_id = request.args.get('v').split('.')[0]
    if 'Range' in request.headers:
        r_range = get_range(request)
        print r_range
        return get_stream('live', video_id, 'video', r_range[0], r_range[1])
    return get_stream('live', video_id, 'video', 0)


@app.route('/download')
def download():
    video_id = request.args.get('v').split('.')[0]
    res_type = request.args.get('type')
    if res_type == 'audio':
        return dl_stream('download', video_id, 'audio')
    else:
        return dl_stream('download', video_id, 'video')


@app.route('/mobile')
def mobile():
    return render_template("mobile.html")


def get_range(request):
    r_range = request.headers.get('Range')
    m = re.match('bytes=(?P<start>\d+)-(?P<end>\d+)?', r_range)
    if m:
        start = m.group('start')
        end = m.group('end')
        start = int(start)
        if end is not None:
            end = int(end)
        return start, end
    else:
        return 0, None


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()  # suppress SSL warning
    app.run(host='local_server_ip', port=9999, threaded=True)


# url = "https://www.youtube.com/watch?v=PAFYgZ0Y2js"
# url = "https://www.youtube.com/watch?v=Bey4XXJAqS8"
# url = "https://www.youtube.com/watch?v=D2LqZAfR_ZE"
