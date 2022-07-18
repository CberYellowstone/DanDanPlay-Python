import hashlib
import mimetypes
import os
import pathlib
import subprocess
import threading
import time
from typing import Iterable, List, Sequence, Tuple, Union

import tqdm
from pymediainfo import MediaInfo

from config import *
from database import *
from unit import universeThread, videoBaseInfoTuple

# from var_dump import var_dump



def checkIfVideo(file_path: str) -> bool:
    if not os.path.isfile(file_path):
        return False
    try:
        guess = mimetypes.guess_type(file_path)[0]
        return guess.startswith('video') if guess is not None else False
    except FileNotFoundError:
        return False


def fiddlerVideosFromFiles(files: Iterable) -> Tuple[Tuple, Tuple]:
    '''input: a list of file path\n
    output: a tuple of (video_paths, not_video_paths)'''
    return tuple(file for file in files if checkIfVideo(file)), tuple(file for file in files if not checkIfVideo(file))


def fiddlerExistVideoPaths(video_paths: Iterable) -> Tuple:
    '''input: a list of file path\n
    output: a Tuple of video_paths which not in the DB'''
    exists = {exist_path[2] for exist_path in getAllVideos()}
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


def getVideoBasicInformation(each_path: str, callback_list:list = None) -> Tuple[str, str, str, str]:
    '''Return a tuple of (hash, duration, size)'''
    _hash = getVideoHash(each_path)
    _duration = getVideoDuration(each_path)
    _filename = getFileName(each_path)
    _size = getFileSize(each_path)
    if callback_list is not None:
        callback_list.append((_hash, _filename, each_path, f'{_size}', f'{_duration}'))
    return _hash, f'{_duration}', _filename, f'{_size}'


def getVideosFromPath(folderPath: str) -> List[str]:
    '''Return a list of video file names in the path, including subfolders'''
    file_list: List[str] = []
    for root, _, files in os.walk(folderPath):
        file_list += (os.path.join(root, path) for path in files if checkIfVideo(os.path.join(root, path)))
    return file_list

def mulitThreadPushVideoBaseInfo2DB(video_paths:Sequence[str], tqdm_obj:Optional[tqdm.tqdm]) -> Tuple[Tuple[str, str, str, str, str], ...]:
    information_list:List[Tuple[str, str, str, str, str]] = []
    locks = [threading.Lock() for _ in range(PUSH_VIDEO_THREAD_NUM)]
    for each_path in video_paths:
        while all(lock.locked() for lock in locks):
            time.sleep(0.1)
        lock = [lock for lock in locks if not lock.locked()][0]
        _filename = getFileName(each_path)
        universeThread(_filename, getVideoBasicInformation, lock, each_path, callback_list=information_list, tqdm_obj=tqdm_obj).start()
    [lock.acquire(blocking=True) for lock in locks]
    return tuple(information_list)

def pushVideoBaseInfo2DB(video_path: Union[str, Sequence[str]], path_is_prechecked: bool = False, show_progress: bool = False, is_dir: bool = False) -> Tuple[bool, Tuple]:
    '''video_path can be a string of single path or a list of path\n
    If success, return True, otherwise return False, and the failed path(s)'''
    if is_dir:
        if isinstance(video_path, str):
            video_path = (video_path,)
        video_path = [each_video_path for each_dir in video_path for each_video_path in getVideosFromPath(each_dir)]# type: ignore
        path_is_prechecked = True
    if isinstance(video_path, str):
        video_path = (video_path,)
    video_path = fiddlerExistVideoPaths(video_path)
    if not path_is_prechecked:
        video_path, faild_path = fiddlerVideosFromFiles(video_path)
    else:
        faild_path = ()
    tqdm_obj = tqdm.tqdm(video_path) if show_progress else None
    if PUSH_VIDEO_THREAD_NUM == 1:
        information_list: List[Tuple[str, str, str, str, str]] = []
        for each_path in video_path:
            _hash, _duration, _filename, _size = getVideoBasicInformation(each_path)
            information_list.append((_hash, _filename, each_path, _size, _duration))
            if show_progress:
                tqdm_obj.set_description(_filename)
                tqdm_obj.update()
    else:
        information_list = mulitThreadPushVideoBaseInfo2DB(video_path, tqdm_obj)# type: ignore
    addVideosIntoDB(information_list)
    return not bool(faild_path), faild_path


def multiThreadCreateThumbnail(_videoBaseInfoTuples:Sequence[videoBaseInfoTuple], size:str = '400*225', show_progress:bool = False, cover:bool = False) -> None:
    locks = [threading.Lock() for _ in range(THUMBNAIL_THREAD_NUM)]
    tqdm_obj = tqdm.tqdm(_videoBaseInfoTuples) if show_progress else None
    for eachTuple in _videoBaseInfoTuples:
        img_path = os.path.join(THUMBNAIL_PATH, f'{eachTuple.hash}{THUMBNAIL_SUFFIX}')
        if(not cover and os.path.exists(img_path)):
            if show_progress:
                tqdm_obj.set_description(f'{eachTuple.fileName}')
                tqdm_obj.update()
            continue
        video_path:str = eachTuple.filePath
        timing:int = int(float(eachTuple.videoDuration)/5)
        args = [FFMPEG_PATH, '-loglevel', 'quiet', '-ss', f'{timing}', '-i', video_path, '-y', '-f', THUMBNAIL_FORMAT, '-t', '1', '-r', '1', '-s', size, img_path]
        while all(lock.locked() for lock in locks):
            time.sleep(0.1)
        lock = [lock for lock in locks if not lock.locked()][0]
        universeThread(eachTuple.fileName, subprocess.run, lock, args, tqdm_obj=tqdm_obj).start()
    [lock.acquire(blocking=True) for lock in locks]


def createThumbnail(_videoBaseInfoTuple: Union[videoBaseInfoTuple, Sequence[videoBaseInfoTuple]] = tuple(each[0] for each in getAllBindedVideos()), size:str = '400*225', show_progress:bool = False, cover:bool = False) -> None: # type: ignore
    if isinstance(_videoBaseInfoTuple, videoBaseInfoTuple):
        _videoBaseInfoTuple = (_videoBaseInfoTuple,)
    if show_progress:
        _videoBaseInfoTuple = tqdm.tqdm(_videoBaseInfoTuple)
    if THUMBNAIL_THREAD_NUM == 1:
        for eachTuple in _videoBaseInfoTuple:
            if show_progress:
                _videoBaseInfoTuple.set_description(f'{eachTuple.fileName}')# type: ignore
            img_path = os.path.join(THUMBNAIL_PATH, f'{eachTuple.hash}{THUMBNAIL_SUFFIX}')
            if(not cover and os.path.exists(img_path)):
                continue
            video_path:str = eachTuple.filePath
            timing:int = int(float(eachTuple.videoDuration)/5)
            subprocess.call([FFMPEG_PATH, '-loglevel', 'quiet', '-ss', f'{timing}', '-i', video_path, '-y', '-f', THUMBNAIL_FORMAT, '-t', '1', '-r', '1', '-s', size, img_path])
    else:
        multiThreadCreateThumbnail(_videoBaseInfoTuple, size, show_progress, cover)
