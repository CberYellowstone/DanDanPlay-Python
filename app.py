import time
from flask import Flask, send_file, jsonify
from config import *
from database import *
from video import *
from dandanplayAPI import *
from unit import *

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<h1>DanDanPlay-Python is running!</h1>"

@app.route('/api/v1/welcome')
@app.route('/welcome')
def retuenWelcome():
    _data = {
        "message": "Hello DandanPlay-Python user!",
        "version": VERSION,
        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
        "tokenRequired": API_TOKEN_REQUIRED
    }
    return _data


@app.route('/api/v1/playlist')
def returnPlaylist():
    return {}


def generateLibrary():
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
                "Duration": eachTuple[0].videoDuration} for eachTuple in getAllBindedVideos()]


@app.route('/api/v1/library')
def returnLibrary():
    return jsonify(generateLibrary())

@app.route('/api/v1/library/<hash>')
@app.route('/api/v1/image/id/<hash>')
def returnImage(hash):
    _path = os.path.join(DATA_PATH,THUMBNAIL_PATH,f'{hash}{THUMBNAIL_SUFFIX}')
    if not os.path.exists(_path):
        return '', 404
    return send_file(_path)


@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response

@app.route('/api/v1/stream/id/<hash>')
@app.route('/api/v1/stream/<hash>')
def returnStream(hash):
    _videoBaseInfoTuple = getVideoFromDB(hash)
    if _videoBaseInfoTuple is None:
        return '', 404
    return send_file(_videoBaseInfoTuple.filePath)


@app.route('/api/v1/comment/id/<hash>')
@app.route('/api/v1/comment/<hash>')
def returnComment(hash):
    _videoBindInfoTuple = getBindingFromDB(hash)
    if _videoBindInfoTuple is None:
        return '', 404
    _path = os.path.join(DATA_PATH,DANMU_PATH,f'{_videoBindInfoTuple.episodeId}.json')
    if not os.path.exists(_path):
        if not DANMU_INSTANT_GET:
            return '', 404
        downloadDanmuFromDandanPlay(_videoBindInfoTuple)
    return covertDanmu(_videoBindInfoTuple.episodeId, 'DanDanPlay-Android')



if __name__ == '__main__':
    app.run('0.0.0.0', threaded=True)