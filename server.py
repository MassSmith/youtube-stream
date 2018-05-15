# -*- coding: utf-8 -*-
# author: gfw-breaker

import re
import json
import sys
import random
import uuid
import pafy
import requests
import lru
import urllib
from flask import Flask
from flask import Response
from flask import stream_with_context
from flask import render_template
from flask import request
from flask import redirect

app = Flask(__name__)
cache = lru.LRUCacheDict(max_size=1000, expiration=60 * 60, concurrent=True)
files = lru.LRUCacheDict(max_size=5000, expiration=60 * 60, concurrent=True)

buffer_size = 1024 * 1024 * 1 # 1MB
block_size = 1024 * 1024 * 4 # 1MB
youtube_url = "https://www.youtube.com/watch?v="

with open(sys.path[0] + '/upstreams.json', 'r') as fp:
	nodes = json.load(fp)


class VideoInfo:

	def __init__(self, id, title, url, audio_url, extension, size):
		self.id = id
		self.title = title
		self.url = url
		self.audio_url = audio_url
		self.extension = extension
		self.size = size


def get_file_by_id(video_id):
	file_name = str(uuid.uuid1()) + '.mp4'
	files[file_name] = video_id
	return file_name


def get_id_by_file(virtual_file):
	return files[virtual_file]


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
	length = min(r_end - start + 1, block_size)
	end = start + length - 1
	print end

	url = '{0}&range={1}-{2}'.format(video_info.url, start, end)
	# print url
	hhds = {'Range': 'bytes={0}-{1}'.format(start, end)}
	req = requests.get(video_info.url, stream=True, verify=False, headers=hhds)
	#req = requests.get(video_info.url, verify=False, headers=hhds)
	# length = len(req.content)
	# print length
	# print req.headers
	# file_name = 'filename=' + video_info.id + '.' + extension
	#file_name = 'attachment; filename=' + urllib.quote(video_info.title.encode('utf-8')) + '.mp4'
	file_name = 'filename=' + video_info.id + '.mp4'

	headers = {
		'Content-Disposition': file_name,
		'Content-Type': 'video/mp4',
		'Content-Length': length,
		'Accept-Ranges': 'bytes',
		'Content-Range': 'bytes {0}-{1}/{2}'.format(start, end, file_size)
	}
	return Response(stream_with_context(req.iter_content(chunk_size=buffer_size)), 206, headers=headers)
	#return Response(req.content, 206, headers=headers)


def get_node():
	idx = random.randint(0, len(nodes) -1 )
	return nodes[idx]

def params(ps):
	pss = ''
	for key in ps:
		value = ps[key]
		pss = pss + '{0}={1}&'.format(key, value)
	if(len(pss) > 0):
		pss = pss[0:len(pss)-1]
	return pss


@app.route('/lb/<path:target_path>')
def lb(target_path):
	node = get_node()
	pss = params(request.args)
	target_url = node + '/' + target_path + '?' + pss
	print 'dispatching request to ' + target_url
	return redirect(target_url, code=302)


@app.route('/vs')
def stream():
	video_id = request.args.get('vv').split('.')[0]
	res_type = request.args.get('type')
	file_id = get_file_by_id(video_id)
	return redirect('/random/' + file_id, code=302)


@app.route('/random/<virtual_file>')
def random_url(virtual_file):
	video_id = files[virtual_file]
	if 'Range' in request.headers:
		r_range = get_range(request)
		print r_range
		return get_stream('live', video_id, 'video', r_range[0], r_range[1])
	return get_stream('live', video_id, 'video', 0)


def get_range(request):
	r_range = request.headers.get('Range')
	if r_range is None:
		return 0, None
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
	app.run(host='0.0.0.0', port=9999, threaded=True)

