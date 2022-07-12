from collections import namedtuple
import mimetypes
from typing import Any, Tuple, Union, Iterable, Generator
from database import *
from config import *
import hashlib
import os
from pymediainfo import MediaInfo
from var_dump import var_dump
# import cv2
import requests
import pathlib
import json
import tqdm

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

videoBaseInfoTuple = namedtuple('videoBaseInfoTuple', 'hash, fileName, filePath, fileSize, videoDuration')
videoBindInfoTuple = namedtuple('videoBindInfoTuple', 'episodeId, animeId, animeTitle, episodeTitle, type, typeDescription, shift', defaults=[0])


def checkIfVideo(file_path: str) -> bool:
    try:
        guess = mimetypes.guess_type(file_path)[0]
        if not guess is None:
            return guess.startswith('video')
        return False
    except FileNotFoundError:
        return False


def fiddlerVideosFromFiles(files: Iterable) -> Tuple[Tuple, Tuple]:
    '''input: a list of file path\n
    output: a tuple of (video_paths, not_video_paths)'''
    return tuple(file for file in files if checkIfVideo(file)), tuple(file for file in files if not checkIfVideo(file))


def fiddlerExistVideoPaths(video_paths: Iterable) -> Tuple:
    '''input: a list of file path\n
    output: a Tuple of video_paths which not in the DB'''
    exists = set([exist_path[2] for exist_path in getAllVideos()])
    return tuple(paths for paths in video_paths if paths not in exists)


def getVideoHash(video_path: str) -> str:
    'path must exist'
    try:
        with open(video_path, "rb") as f:
            # 16 * 1024 * 1024 = 16777216
            return hashlib.md5(f.read(16777216)).hexdigest().upper()
    except FileNotFoundError:
        return ''


def getVideoDuration(video_path: str) -> int:
    '''path must exist'''
    try:
        _videoinfo = MediaInfo.parse(video_path)
    except FileNotFoundError:
        return -1
    # var_dump(_videoinfo.video_tracks[0].duration)
    return int(float(_videoinfo.video_tracks[0].duration)/1000)


def getFileName(path: str, with_extension: bool = False) -> str:
    '''path must exist'''
    try:
        return pathlib.Path(path).name if with_extension else pathlib.Path(path).stem
    except FileNotFoundError:
        return ''


def getFileSize(path):
    '''path must exist'''
    try:
        return os.path.getsize(path)
    except FileNotFoundError:
        return -1


def vaildJSON(json_str: str) -> bool:
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


def queryDandanPlay(video_path: str) -> Tuple[bool, Any]:
    '''If matched, return a tuple of (True, videoBindInfoTuple),\n 
    otherwise return a tuple of (False, Tuple[videoBindInfoTuple])
    '''
    _apiurl = 'https://api.acplay.net/api/v2/match'
    _data = {
        "fileName": getFileName(video_path),
        "fileHash": getVideoHash(video_path),
        "fileSize": getFileSize(video_path),
        "videoDuration": getVideoDuration(video_path),
        "matchMode": "hashAndFileName"
    }
    for _ in range(3):
        #TODO: Logging
        try:
            _context = requests.post(
                _apiurl, json=_data, verify=False, timeout=10)
            break
        except requests.exceptions.ConnectTimeout:
            continue
    else:
        return False, None
    _dict = _context.json()
    if not _dict['success']:
        raise LookupError(_dict['errorMessage'])
    if _dict['isMatched']:
        return True, videoBindInfoTuple(**_dict['matches'][0])
    else:
        return False, tuple(videoBindInfoTuple(**eachMatch) for eachMatch in _dict['matches'])


def pushVideoBaseInfo2DB(video_path: Union[str, Iterable], path_is_prechecked: bool = False, show_progress: bool = False) -> Tuple[bool, Union[str, Iterable, None]]:
    '''video_path can be a string of single path or a list of path\n
    If success, return True, otherwise return False, and the failed path(s)'''
    if isinstance(video_path, str):
        if not path_is_prechecked and not checkIfVideo(video_path):
            return False, video_path
        _hash = getVideoHash(video_path)
        _duration = getVideoDuration(video_path)
        _filename = getFileName(video_path)
        _size = getFileSize(video_path)
        addVideoIntoDB(_hash, _filename, video_path, f'{_size}', f'{_duration}')
        return True, None
    else:
        video_path = fiddlerExistVideoPaths(video_path)
        if not path_is_prechecked:
            video_path, faild_path = fiddlerVideosFromFiles(video_path)
        else:
            faild_path = ()
        information_list: List[Tuple[str, str, str, str, str]] = []
        if show_progress:
            video_path = tqdm.tqdm(video_path)
        for each_path in video_path:
            _hash = getVideoHash(each_path)
            # _hash = ''
            _duration = getVideoDuration(each_path)
            _filename = getFileName(each_path)
            _size = getFileSize(each_path)
            information_list.append(
                (_hash, _filename, each_path, f'{_size}', f'{_duration}'))
            if show_progress:
                video_path.set_description(f'{_filename}')  # type: ignore
        addVideosIntoDB(information_list)
        return not bool(faild_path), faild_path

# TODO: Add Logging


def bindVideosIfIsMatched() -> Tuple[tuple, tuple]:
    '''Try to search the not-binded videos in the DB,\n
    if Dandanplay API return a 'isMatched' flag,\n
    then auto bind the video. Otherwise, return it in the not-binded videos.
    Returns: Tuple[Tuple[videoBaseInfoTuple, videoBindInfoTuple], Tuple[videoBaseInfoTuple, Tuple[videoBindInfoTuple]]]
    '''
    binded_videos = []
    need_manual_bind_videos = []
    for each_video_baseinfo in (videoBaseInfoTuple._make(eachBaseInfo) for eachBaseInfo in getAllUnBindedVideos()):
        _is_matched, _matches = queryDandanPlay(each_video_baseinfo.filePath)
        if _is_matched:
            binded_videos.append((each_video_baseinfo, _matches))
            addBindingIntoDB(each_video_baseinfo.hash, _matches.animeId, _matches.animeTitle, _matches.episodeId, _matches.episodeTitle, _matches.type, _matches.typeDescription)
        else:
            need_manual_bind_videos.append((each_video_baseinfo, _matches))
    return tuple(binded_videos), tuple(need_manual_bind_videos)


def downloadDanmuFromDandanPlay(episodeId: int, _from: int = 0, with_related: bool = True, ch_convert: int = 1) -> bool:
    '''Download danmu from Dandanplay,\n
    with_related: If True, download related danmu.\n
    ch_convert: 0: no convert, 1: convert to simple chinese, 2: convert to traditional chinese
    '''
    danmu_file_path = os.path.join(DANMU_PATH, f'{episodeId}.json')
    # TODO: Add Logging
    _apiurl = f'https://api.acplay.net/api/v2/comment/{episodeId}?from={_from}&withRelated={with_related}&chConvert={ch_convert}'
    _context = requests.get(_apiurl, verify=False).content.decode('utf-8')
    if not vaildJSON(_context):
        return False
    with open(danmu_file_path, 'w', encoding='utf-8') as f:
        f.write(_context)
    return True
