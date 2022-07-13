import json
import threading
from typing import Callable, Optional

import tqdm
# from var_dump import var_dump


def vaildJSON(json_str: str) -> bool:
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False


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
