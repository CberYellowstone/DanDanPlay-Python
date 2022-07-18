import contextlib
import os

from config import *
from database import initDB


def delAll():
    with contextlib.suppress(FileNotFoundError):
        os.remove(DATA_PATH)


def initFolder():
    if os.path.exists(DATA_PATH) and not os.path.isdir(DATA_PATH):
        os.replace(DATA_PATH, f'{DATA_PATH}.bak')
    for each_path in DANMU_PATH, THUMBNAIL_PATH:
        if os.path.exists(each_path) and not os.path.isdir(each_path):
            # TODO: Logging
            os.replace(each_path, f'{each_path}.bak')
        with contextlib.suppress(FileExistsError):
            os.makedirs(os.path.join(each_path))

def init():
    initFolder()
    initDB()

if __name__ == '__main__':
    init()
