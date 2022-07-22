import functools
import time

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
# from var_dump import var_dump

from auth import *
from config import CONFIG
from dandanplayAPI import *
from database import *
from unit import *
from video import *

app = Flask(__name__)
CORS(app, supports_credentials=True)


def return401(*args, **kwargs):
    return '', 401

def checkAuth(pass_name:bool = False):
    def checkAuthWrapper(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not CONFIG.API_TOKEN_REQUIRED:
                return func(*args, **kwargs)
            _token = request.headers.get('Authorization', '').lstrip('Bearer').lstrip()
            _state, _usernameOrMessage = vaildToken(_token)
            _state2 = request.args.get('token', '') == CONFIG.ONCE_SECRET
            if not any((_state, _state2)):
                return return401(*args, **kwargs)
            if pass_name:
                return func(*args, **kwargs, username=_usernameOrMessage)
            return func(*args, **kwargs)
        return wrapper
    return checkAuthWrapper


@app.route("/")
def root():
    return "<h1>DanDanPlay-Python is running!</h1>"

@app.route('/api/v1/welcome')
@app.route('/welcome')
def retuenWelcome():
    return {
        "message": "Hello DandanPlay-Python User!",
        "version": CONFIG.VERSION,
        "time": time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(time.time())
        ),
        "tokenRequired": CONFIG.API_TOKEN_REQUIRED,
    }


@app.route('/api/v1/playlist')
@checkAuth()
def returnPlaylist():
    return jsonify({})


def generateLibrary(_hash: Optional[str] = None) -> List[dict]:
    _bindings = getAllBindedVideos() if _hash is None else getSpecificBindedVideo(_hash)
    default_time = '0001-01-01T00:00:00'
    return [{
                "AnimeId": eachTuple[1].animeId,
                "EpisodeId": eachTuple[1].episodeId,
                "AnimeTitle": eachTuple[1].animeTitle,
                "EpisodeTitle": eachTuple[1].episodeTitle,
                "Id": eachTuple[0].hash,
                "Hash": eachTuple[0].hash,
                "Name": getFileName(eachTuple[0].filePath, with_extension=True),
                "Path": f'Y:\\{eachTuple[1].animeTitle}\\{getFileName(eachTuple[0].filePath, with_extension=True)}',
                "Size": eachTuple[0].fileSize,
                "Rate": 0,
                "IsStandalone": False,
                "Created": default_time,
                "LastMatch": default_time,
                "LastPlay": eachTuple[2],
                "LastThumbnail": None,
                "Duration": eachTuple[0].videoDuration} for eachTuple in _bindings]


@app.route('/api/v1/library')
@checkAuth()
def returnLibrary():
    return jsonify(generateLibrary())


@app.route('/api/v1/image/<_hash>')
@app.route('/api/v1/image/id/<_hash>')
def returnImage(_hash):
    _path = os.path.join(CONFIG.DATA_PATH,CONFIG.THUMBNAIL_PATH,f'{_hash}{CONFIG.THUMBNAIL_SUFFIX}')
    if not os.path.exists(_path):
        if not CONFIG.THUMBNAIL_INSTANT_CREATE:
            return '', 404
        _videoBaseInfoTuple = getVideoFromDB(_hash)
        if _videoBaseInfoTuple is None:
            return '', 404
        createThumbnail(_videoBaseInfoTuple)
    return send_file(_path) 


@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response

@app.route('/api/v1/stream/id/<_hash>')
@app.route('/api/v1/stream/<_hash>')
@checkAuth()
def returnStream(_hash):
    _videoBaseInfoTuple = getVideoFromDB(_hash)
    return send_file(_videoBaseInfoTuple.filePath) if (_videoBaseInfoTuple is not None) else ('', 404)


@app.route('/api/v1/comment/id/<_hash>')
@app.route('/api/v1/comment/<_hash>')
@checkAuth()
def returnAPIComment(_hash):
    _videoBindInfoTuple = getBindingFromDB(_hash)
    if _videoBindInfoTuple is None:
        return '', 404
    _path = os.path.join(CONFIG.DATA_PATH,CONFIG.DANMU_PATH,f'{_videoBindInfoTuple.episodeId}.json')
    if not os.path.exists(_path):
        if not CONFIG.DANMU_INSTANT_GET:
            return '', 404
        downloadDanmuFromDandanPlay(_videoBindInfoTuple)
    return covertDanmu(_videoBindInfoTuple.episodeId, 'DanDanPlay-Android')


@app.route('/api/v1/auth', methods=['POST'])
def dealAuth():
    _body = request.get_json()
    _state, _message = vaildLogin(_body['userName'], _body['password'])
    return (
        jsonify(
            {
                "id": generateUUID(_body['userName']),
                "userName": _body['userName'],
                "token": generateToken(_body['userName']),
                "error": "",
            }
        )
        if _state
        else jsonify(
            {"id": "", "userName": "", "token": "", "error": _message}
        )
    )


@app.route('/api/v1/playerconfig/<_hash>')
@checkAuth()
def returnPlayCONFIG(_hash):
    _videoInfoTuple = getSpecificBindedVideo(_hash)
    if _videoInfoTuple[0] is None:
        return '', 404
    _token_str = f"?token={CONFIG.ONCE_SECRET}"
    return jsonify({"id": _hash,
    "video": generateLibrary(_videoInfoTuple[0][0].hash)[0],
    "videoUrl": f"/api/v1/stream/id/{_hash}{_token_str}",
    "imageUrl": f"/api/v1/image/id/{_hash}{_token_str}",
    "vttUrl": f"/api/v1/subtitle/vtt/{_hash}{_token_str}",
    "color": "#000000",
    "dmDuration": "9s",
    "dmSize": "25px",
    "dmArea": "83%",
    "videoFiles":[{
        "id": eachTuple[0].hash,
        "episodeTitle": eachTuple[1].episodeTitle,
        "fileName": getFileName(eachTuple[0].filePath, with_extension=True),
        "isCurrent": eachTuple[0].hash == _hash,
    } for eachTuple in sorted(getSpecificAnimeBindedVideos(_videoInfoTuple[0][1].animeId), key=lambda x: x[1].episodeId)]})


# http://127.0.0.1:4444/api/v1/dplayer/v3/?id=e90fdbfc-541a-41e1-8aac-ef2a82076ca8
@app.route('/api/v1/dplayer/v3/')
def returnWebComment():
    _hash = request.args.get('id', '')
    _videoBindInfoTuple = getBindingFromDB(_hash)
    if _videoBindInfoTuple is None:
        return '', 404
    _path = os.path.join(CONFIG.DATA_PATH,CONFIG.DANMU_PATH,f'{_videoBindInfoTuple.episodeId}.json')
    if not os.path.exists(_path):
        if not CONFIG.DANMU_INSTANT_GET:
            return '', 404
        downloadDanmuFromDandanPlay(_videoBindInfoTuple)
    return covertDanmu(_videoBindInfoTuple.episodeId, 'Web')

def run(host:str = '0.0.0.0', port:int = 5000):
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == '__main__':
    run()
