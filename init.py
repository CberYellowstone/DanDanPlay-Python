import contextlib
from config import *
from database import initDB
import os

def delAll():
    with contextlib.suppress(FileNotFoundError):
        os.remove(DB_PATH)

def initFolder():
    if os.path.exists(DANMU_PATH) and not os.path.isdir(DANMU_PATH):
        # TODO: Logging
        os.replace(DANMU_PATH, f'{DANMU_PATH}.bak')
    with contextlib.suppress(FileExistsError):
        os.mkdir(os.path.join(DANMU_PATH))


initDB()
initFolder()
