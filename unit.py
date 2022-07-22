import json
import os
import threading
import xml.etree.cElementTree as ET
from collections import namedtuple
from typing import Callable, Optional

import tqdm

from config import CONFIG

# from var_dump import var_dump

videoBaseInfoTuple = namedtuple('videoBaseInfoTuple', 'hash, fileName, filePath, fileSize, videoDuration')
videoBindInfoTuple = namedtuple('videoBindInfoTuple', 'animeId, episodeId, animeTitle, episodeTitle, type, typeDescription, shift', defaults=(0,))


class universeThread(threading.Thread):
    def __init__(self, name: str, func: Callable, lock: threading.Lock, *args, tqdm_obj: Optional[tqdm.tqdm] = None, **kw):
        threading.Thread.__init__(self)
        self.name, self.func, self.lock, self.tqdm_obj, self.args, self.kw = name, func, lock, tqdm_obj, args, kw

    def run(self):
        self.lock.acquire()
        if self.tqdm_obj is not None:
            self.tqdm_obj.set_description(self.name)
        self.func(*self.args, **self.kw)
        if self.tqdm_obj is not None:
            self.tqdm_obj.update()
        self.lock.release()


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
