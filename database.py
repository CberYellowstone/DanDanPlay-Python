from typing import List, Optional, Sequence, Tuple
from config import *
import sqlite3
from contextlib import closing


# TODO:last_watch_time
def initDB():
    if os.path.exists(DB_PATH):
        return
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS Video (hash TEXT PRIMARY KEY, fileName TEXT, filePath TEXT, fileSize TEXT, videoDuration TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS Binding (hash TEXT PRIMARY KEY, animeId INTEGER, episodeId INTEGER, animeTitle TEXT, episodeTitle TEXT, type TEXT, typeDescription TEXT)")
            connection.commit()

def clearDB():
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("DELETE FROM Video")
            cursor.execute("DELETE FROM Binding")
            connection.commit()

def addVideoIntoDB(hash: str, fileName: str, filePath: str, fileSize: str, videoDuration: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT OR IGNORE INTO Video VALUES (?, ?, ?, ?, ?)", (hash, fileName, filePath, fileSize, videoDuration))
            connection.commit()


def addVideosIntoDB(videos: Sequence[Tuple[str, str, str, str, str]]) -> None:
    '''eachTuple: [0] hash: str, [1] fileName: str, [2] filePath: str, [3] fileSize: str, [4] videoDuration: str'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            for video in videos:
                cursor.execute("INSERT OR IGNORE INTO Video VALUES (?, ?, ?, ?, ?)", video)
            connection.commit()

def addBindingIntoDB(hash: str, animeId: int, episodeId: int, animeTitle: str, episodeTitle: str, type: str, typeDescription: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT OR IGNORE INTO Binding VALUES (?, ?, ?, ?, ?, ?, ?)", (hash, animeId, episodeId, animeTitle, episodeTitle, type, typeDescription))
            connection.commit()

def addBindingsIntoDB(bindings: Sequence[Tuple[str, int, int, str, str, str, str]]) -> None:
    '''eachTuple: [0] hash, [1] animeId, [2] episodeId, [3] animeTitle, [4] episodeTitle, [5] type, [6] typeDescription'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            for binding in bindings:
                cursor.execute("INSERT OR IGNORE INTO Binding VALUES (?, ?, ?, ?, ?, ?, ?)", binding)
            connection.commit()

def getVideoFromDB(hash: str) -> Optional[Tuple[str, str, str, str, str]]:
    '''[0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video WHERE hash=?", (hash,))
            return cursor.fetchone()

def getAllVideos() -> List[Tuple[str, str, str, str, str]]:
    '''eachTuple: [0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video")
            return cursor.fetchall()

def checkIfVideoBinded(hash: str) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Binding WHERE hash=?", (hash,))
            return bool(cursor.fetchone())

def getAllBindedVideos():
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Binding")
            return cursor.fetchall()

def getAllUnBindedVideos() -> List[Tuple[str, str, str, str, str]]:
    '''eachTuple: [0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video WHERE hash NOT IN (SELECT hash FROM Binding)")
            return cursor.fetchall()

def getBindingFromDB(hash: str):
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Binding WHERE hash=?", (hash,))
            return cursor.fetchone()
