import os
import threading
from collections import namedtuple
from typing import Any, Callable, Optional

import click
import tqdm

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


class AbsPath(click.ParamType):
    name = 'AbsPath'

    def __init__(self) -> None:
        super().__init__()

    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        if not os.path.isabs(value):
            self.fail('请输入绝对路径', param, ctx)
        return super().convert(value, param, ctx)
