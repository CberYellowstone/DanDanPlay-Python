import html
import json
import os
import threading
import time
import xml.etree.cElementTree as ET
from typing import List, Optional, Sequence, Tuple, Union

import requests
import tqdm
import urllib3

from .config import CONFIG
from .database import addBindingsIntoDB, getAllUnBindedVideos
from .unit import universeThread, videoBaseInfoTuple, videoBindInfoTuple

from var_dump import var_dump


urllib3.disable_warnings()


def queryDandanPlay(_videoBaseInfoTuple: videoBaseInfoTuple) -> Tuple[bool, Optional[Union[videoBindInfoTuple, Tuple[videoBindInfoTuple, ...]]]]:
    '''If matched, return a tuple of (True, videoBindInfoTuple),\n 
    otherwise return a tuple of (False, Tuple[videoBindInfoTuple] | None)
    '''
    _apiurl = 'https://api.dandanplay.net/api/v2/match'
    _data = {
        "fileName": _videoBaseInfoTuple.fileName,
        "fileHash": _videoBaseInfoTuple.hash,
        "fileSize": _videoBaseInfoTuple.fileSize,
        "videoDuration": _videoBaseInfoTuple.videoDuration,
        "matchMode": "hashAndFileName"
    }
    for _ in range(3):
        #TODO: Logging
        try:
            _context = requests.post(_apiurl, json=_data, verify=False)
            _dict = json.loads(html.unescape(_context.content.decode('utf-8')))
            break
        except requests.exceptions.ConnectTimeout:
            time.sleep(1)
            continue
        except json.JSONDecodeError:
            time.sleep(1)
            continue
    else:
        return False, None
    if not _dict['success']:
        raise LookupError(_dict['errorMessage'])
    if _dict['isMatched']:
        return True, videoBindInfoTuple(**_dict['matches'][0])
    else:
        return False, tuple(videoBindInfoTuple(**eachMatch) for eachMatch in _dict['matches'])


def singleThreadDownloadDanmu(_from: int, with_related:bool, ch_convert:int, skips:List, eachVideoBindInfoTuple:videoBindInfoTuple, danmu_file_path) -> None:
    for _ in range(3):
        try:
            _apiurl = f'https://api.dandanplay.net/api/v2/comment/{eachVideoBindInfoTuple.episodeId}?from={_from}&withRelated={with_related}&chConvert={ch_convert}'
            _rep = requests.get(_apiurl, verify=False)
            _rep.json()
            break
        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.InvalidJSONError:
            continue
    else:
        skips.append(eachVideoBindInfoTuple)
        return
    try:
        _context = _rep.content.decode('utf-8')
        with open(danmu_file_path, 'w', encoding='utf-8') as f:
            f.write(_context)
    except Exception:
        skips.append(eachVideoBindInfoTuple)


def multiThreadDownloadDanmuFromDandanPlay(_videoBindInfoTuple:Sequence[videoBindInfoTuple], _from: int, with_related: bool, ch_convert: int, update:bool, show_progress:bool) -> Tuple[bool, Tuple]:
    locks = [threading.Lock() for _ in range(CONFIG.THUMBNAIL_THREAD_NUM)]
    tqdm_obj = tqdm.tqdm(_videoBindInfoTuple) if show_progress else None
    skips:List[videoBindInfoTuple] = []
    for eachVideoBindInfoTuple in _videoBindInfoTuple:
        danmu_file_path = os.path.join(CONFIG.DANMU_PATH, f'{eachVideoBindInfoTuple.episodeId}.json')
        _name = f'{eachVideoBindInfoTuple.animeTitle} - {eachVideoBindInfoTuple.episodeTitle}'
        if(not update and os.path.exists(danmu_file_path)):
            if tqdm_obj is not None:
                tqdm_obj.set_description(_name)  # type: ignore
                tqdm_obj.update()
            continue
        while all(lock.locked() for lock in locks):
            time.sleep(0.1)
        lock = [lock for lock in locks if not lock.locked()][0]
        universeThread(_name, singleThreadDownloadDanmu, lock, _from, with_related, ch_convert, skips, eachVideoBindInfoTuple, danmu_file_path, tqdm_obj=tqdm_obj).start()
    [lock.acquire(blocking=True) for lock in locks]
    return bool(skips), tuple(skips)

# TODO: Add Logging
def downloadDanmuFromDandanPlay(_videoBindInfoTuple: Union[videoBindInfoTuple, Sequence[videoBindInfoTuple]], _from: int = 0, with_related: bool = True, ch_convert: int = 1, update: bool = False, show_progress: bool = False) -> Tuple[bool, Tuple]:
    '''Download danmu from Dandanplay,\n
    with_related: If True, download related danmu.\n
    ch_convert: 0: no convert, 1: convert to simple chinese, 2: convert to traditional chinese
    '''
    if isinstance(_videoBindInfoTuple, videoBindInfoTuple):
        _videoBindInfoTuple = (_videoBindInfoTuple,)

    if CONFIG.DANMU_DOWNLOAD_THREAD_NUM != 1:
        return multiThreadDownloadDanmuFromDandanPlay(_videoBindInfoTuple, _from, with_related, ch_convert, update, show_progress)
    if show_progress:
        _videoBindInfoTuple = tqdm.tqdm(_videoBindInfoTuple)  # type: ignore
    skips: List[videoBindInfoTuple] = []
    for eachVideoBindInfoTuple in _videoBindInfoTuple:
        if show_progress:
            _videoBindInfoTuple.set_description(f'{eachVideoBindInfoTuple.animeTitle} - {eachVideoBindInfoTuple.episodeTitle}')  # type: ignore
        danmu_file_path = os.path.join(CONFIG.DANMU_PATH, f'{eachVideoBindInfoTuple.episodeId}.json')
        if(not update and os.path.exists(danmu_file_path)):
            continue
        singleThreadDownloadDanmu(_from, with_related, ch_convert, skips, eachVideoBindInfoTuple, danmu_file_path)
    return not bool(skips), tuple(skips)


def multiThreadBindVideosIfIsMached(each_video_baseinfo_group: Sequence[videoBaseInfoTuple], tqdm_obj: Optional[tqdm.tqdm] = None) -> Tuple[List[Tuple[str, videoBindInfoTuple]], List[Tuple[videoBaseInfoTuple, videoBindInfoTuple]], List[Tuple[videoBaseInfoTuple, Tuple[videoBindInfoTuple]]]]:
    '''Returns: \n[0]: List[Tuple[str, videoBindInfoTuple]], \n[1]: List[Tuple[videoBaseInfoTuple, videoBindInfoTuple]], \n[2]: List[Tuple[videoBaseInfoTuple, Tuple[videoBindInfoTuple]]]'''
    def singleThread(_videoBaseInfoTuple: videoBaseInfoTuple, videoBindInfoTuples: List, binded_list: List, need_manual_bind_list: List) -> None:
        _is_matched, _matches = queryDandanPlay(_videoBaseInfoTuple)
        if _is_matched:
            videoBindInfoTuples.append((_videoBaseInfoTuple.hash, _matches))
            binded_list.append((_videoBaseInfoTuple, _matches))  # type: ignore
        else:
            need_manual_bind_list.append((_videoBaseInfoTuple, _matches))
    video_bind_infos: List[Tuple[str, videoBindInfoTuple]] = []
    binded_videos: List[Tuple[videoBaseInfoTuple, videoBindInfoTuple]] = []
    need_manual_bind_videos: List[Tuple[videoBaseInfoTuple, Tuple[videoBindInfoTuple]]] = []
    locks = [threading.Lock() for _ in range(CONFIG.MATCH_VIDEO_THREAD_NUM)]
    for each_video_baseinfo in each_video_baseinfo_group:
        while all(lock.locked() for lock in locks):
            time.sleep(0.1)
        lock = [lock for lock in locks if not lock.locked()][0]
        universeThread(each_video_baseinfo.fileName, singleThread, lock, each_video_baseinfo, video_bind_infos, binded_videos, need_manual_bind_videos, tqdm_obj=tqdm_obj).start()
    [lock.acquire(blocking=True) for lock in locks]
    return video_bind_infos, binded_videos, need_manual_bind_videos


# TODO: Add Logging
def bindVideosIfIsMatched(show_progress:bool = False, only_ignore:bool = False) -> Tuple[tuple, tuple]:
    '''Try to search the not-binded videos in the DB,\n
    if Dandanplay API return a 'isMatched' flag,\n
    then auto bind the video. Otherwise, return it in the not-binded videos.
    Returns: Tuple[Tuple[videoBaseInfoTuple, videoBindInfoTuple], Tuple[videoBaseInfoTuple, Tuple[videoBindInfoTuple]]]
    '''
    binded_videos = []
    need_manual_bind_videos = []
    all_videos = [videoBaseInfoTuple._make(
        eachBaseInfo) for eachBaseInfo in getAllUnBindedVideos(only_ignore)]
    tqdm_obj = tqdm.tqdm(all_videos) if show_progress else None

    for each_video_baseinfo_group in [all_videos[i:i + CONFIG.MATCH_VIDEO_SPLIT_NUM] for i in range(0, len(all_videos), CONFIG.MATCH_VIDEO_SPLIT_NUM)]:
        if CONFIG.MATCH_VIDEO_THREAD_NUM == 1:
            videoBindInfoTuples: List[Tuple[str, videoBindInfoTuple]] = []
            for each_video_baseinfo in each_video_baseinfo_group:
                if show_progress:
                    tqdm_obj.set_description(f'{each_video_baseinfo.fileName}')  # type: ignore
                    tqdm_obj.update()  # type: ignore

                _is_matched, _matches = queryDandanPlay(each_video_baseinfo)
                if _is_matched:
                    binded_videos.append((each_video_baseinfo, _matches))
                    videoBindInfoTuples.append((each_video_baseinfo.hash, _matches))  # type: ignore
                else:
                    need_manual_bind_videos.append((each_video_baseinfo, _matches))
        else:
            videoBindInfoTuples, binded_video, need_manual_bind_video = multiThreadBindVideosIfIsMached(
                each_video_baseinfo_group, tqdm_obj=tqdm_obj)
            binded_videos += binded_video
            need_manual_bind_videos += need_manual_bind_video
        addBindingsIntoDB(videoBindInfoTuples)
    return tuple(binded_videos), tuple(need_manual_bind_videos)


def covert2XML(episodeId: int) -> str:
    root = ET.Element('i', {'xmlns:xsd': 'http://www.w3.org/2001/XMLSchema', 'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'})
    ET.SubElement(root, 'chatserver').text = 'chat.bilibili.com'
    ET.SubElement(root, 'chatid').text = '10000'
    ET.SubElement(root, 'mission').text = '0'
    ET.SubElement(root, 'maxlimit').text = '8000'
    ET.SubElement(root, 'source').text = 'e-r'
    ET.SubElement(root, 'ds').text = '931869000'
    ET.SubElement(root, 'de').text = '937654881'
    ET.SubElement(root, 'max_count').text = '8000'
    with open(os.path.join(CONFIG.DANMU_PATH, f'{episodeId}.json'), 'r', encoding='utf-8') as f:
        _json = json.loads(f.read())
        for eachDanmu in _json['comments']:
            parameters = eachDanmu['p'].split(',')
            ET.SubElement(root, 'd', {'p':f'{parameters[0]},{parameters[1]},25,{parameters[2]},-639093600,0,0,0'}).text = eachDanmu['m']
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def covert2JSON(episodeId: int) -> str:
    with open(os.path.join(CONFIG.DANMU_PATH, f'{episodeId}.json'), 'r', encoding='utf-8') as f:
        _json = json.loads(f.read())
        _list = [[float(eachDanmu['p'].split(',')[0]), 1 if int(eachDanmu['p'].split(',')[1]) == 5 else 0, int(eachDanmu['p'].split(',')[2]), eachDanmu['p'].split(',')[3], eachDanmu['m']] for eachDanmu in _json['comments']]
        return json.dumps({'code':0, 'data':_list})


def covertDanmu(episodeId: int, type:str) -> str:
    '''type: "DanDanPlay-Android" or "Web"'''
    if type == 'DanDanPlay-Android':
        return covert2XML(episodeId)
    elif type == 'Web':
        return covert2JSON(episodeId)
    else:
        raise Exception('type error')


def searchDanDanPlay(key_word:str) -> Tuple[bool, Tuple[videoBindInfoTuple, ...]]:
    '''Iuput a key word, and return the result from dandanplay-api. \n\nReturn: hasMore: bool, Tuple[videoBindInfoTuple]'''
    _apiurl = f'https://api.dandanplay.net/api/v2/search/episodes?anime={html.escape(key_word)}&episode='
    for _ in range(3):
        #TODO: Logging
        try:
            _context = requests.get(_apiurl, verify=False)
            _dict = json.loads(html.unescape(_context.content.decode('utf-8')))
            break
        except requests.exceptions.ConnectTimeout:
            time.sleep(1)
            continue
        except requests.exceptions.InvalidJSONError:
            time.sleep(1)
            continue
    else:
        return False, () #type: ignore
    _hasMore:bool = _dict['hasMore']
    _videoBindInfoTuples = tuple(videoBindInfoTuple(_eachDict['animeId'], _episodes['episodeId'], _eachDict['animeTitle'], _episodes['episodeTitle'], _eachDict['type'], _eachDict['typeDescription']) for _eachDict in _dict['animes'] for _episodes in _eachDict['episodes'])
    return _hasMore, _videoBindInfoTuples