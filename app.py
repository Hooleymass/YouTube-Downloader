from flask import Flask, request, jsonify, make_response, render_template
from werkzeug.exceptions import BadRequest
import subprocess
import json
import time

app = Flask(__name__)

CACHE_TIMEOUT = 60  # Cache timeout in seconds
CACHE_FILE = 'cache.json'

def load_cache():
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_cache(cache_data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f)

def get_video_link(video_input):
    cache_data = load_cache()
    if video_input in cache_data and time.time() - cache_data[video_input]['timestamp'] < CACHE_TIMEOUT:
        return cache_data[video_input]

    is_id = False
    if 'youtube.com/watch?v=' in video_input:
        video_id = video_input.split('youtube.com/watch?v=')[1].split('&')[0]
    else:
        video_id = video_input
        is_id = True

    if is_id:
        video_url = f'https://www.youtube.com/watch?v={video_id}'
    else:
        video_url = video_input

    cmd = f'yt-dlp -g {video_url}'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    video_link = result.stdout.decode('utf-8').strip()

    cache_data[video_input] = {
        'video_link': video_link,
        'expiry_time': int(time.time()) + CACHE_TIMEOUT,
        'timestamp': time.time()
    }
    save_cache(cache_data)
    return cache_data[video_input]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_video_link', methods=['GET'])
def get_video_link_api():
    try:
        video_input = request.args.get('video_input')
        if not video_input:
            raise BadRequest('Missing video_input parameter')

        video_info = get_video_link(video_input)
        response = {'video_link': video_info['video_link'], 'expiry_time': video_info['expiry_time']}
        return jsonify(response)

    except Exception as e:
        error_message = str(e)
        return make_response(jsonify({'error': error_message}), 400)

if __name__ == '__main__':
    app.run(debug=True)

