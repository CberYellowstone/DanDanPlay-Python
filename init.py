import contextlib
from config import *
from database import initDB
import os

def delAll():
    with contextlib.suppress(FileNotFoundError):
        os.remove(DB_PATH)

def initFolder():
    for each_path in DANMU_PATH, THUMBNAIL_PATH:
        if os.path.exists(each_path) and not os.path.isdir(each_path):
            # TODO: Logging
            os.replace(each_path, f'{each_path}.bak')
        with contextlib.suppress(FileExistsError):
            os.mkdir(os.path.join(each_path))

if __name__ == '__main__':
    initDB()
    initFolder()
