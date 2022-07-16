import time
from typing import Optional, Sequence, Tuple
from config import *
import sqlite3
from contextlib import closing
from unit import videoBaseInfoTuple, videoBindInfoTuple


def initDB():
    if os.path.exists(DB_PATH):
        return
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS Video (hash TEXT PRIMARY KEY, fileName TEXT, filePath TEXT, fileSize TEXT, videoDuration TEXT, lastWatchTime INTEGER DEFAULT -1)")
            cursor.execute("CREATE TABLE IF NOT EXISTS Binding (hash TEXT PRIMARY KEY, animeId INTEGER, episodeId INTEGER, animeTitle TEXT, episodeTitle TEXT, type TEXT, typeDescription TEXT)")
            connection.commit()


def clearDB(part: str = 'all') -> None:
    '''part: 'all' or 'video' or 'binding'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            if part == 'all' or part == 'video':
                cursor.execute("DELETE FROM Video")
            if part == 'all' or part == 'binding':
                cursor.execute("DELETE FROM Binding")
            connection.commit()


def addVideoIntoDB(hash: str, fileName: str, filePath: str, fileSize: str, videoDuration: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT OR IGNORE INTO Video(hash, fileName, filePath, fileSize, videoDuration) VALUES (?, ?, ?, ?, ?)", (hash, fileName, filePath, fileSize, videoDuration))
            connection.commit()


def addVideosIntoDB(videos: Sequence[Tuple[str, str, str, str, str]]) -> None:
    '''eachTuple: [0] hash: str, [1] fileName: str, [2] filePath: str, [3] fileSize: str, [4] videoDuration: str'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            for video in videos:
                cursor.execute("INSERT OR IGNORE INTO Video(hash, fileName, filePath, fileSize, videoDuration) VALUES (?, ?, ?, ?, ?)", video)
            connection.commit()


def addBindingIntoDB(hash: str, _videoBindInfoTuple: videoBindInfoTuple) -> None:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT OR IGNORE INTO Binding VALUES (?, ?, ?, ?, ?, ?, ?)", (hash, *_videoBindInfoTuple[:6]))
            connection.commit()


def addBindingsIntoDB(bindings: Sequence[Tuple[str, videoBindInfoTuple]]) -> None:
    '''eachTuple: [0] hash, [1] videoBindInfoTuple'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            for binding in bindings:
                cursor.execute("INSERT OR IGNORE INTO Binding VALUES (?, ?, ?, ?, ?, ?, ?)", (binding[0], *(binding[1][:6])))
            connection.commit()


def getVideoFromDB(hash: str) -> Optional[videoBaseInfoTuple]:
    '''videoBindInfoTuple: [0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video WHERE hash=?", (hash,))
            return videoBaseInfoTuple._make(cursor.fetchone()[:5])


def getAllVideos() -> Tuple[videoBaseInfoTuple, ...]:
    '''videoBindInfoTuple: [0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video")
            return tuple(videoBaseInfoTuple._make(eachTuple[:5]) for eachTuple in cursor.fetchall())


def checkIfVideoBinded(hash: str) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Binding WHERE hash=?", (hash,))
            return cursor.fetchone() is None


def getAllBindedVideos() -> Tuple[Tuple[str, videoBindInfoTuple], ...]:
    '''[0] hash, [1] videoBindInfoTuple'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Binding")
            return tuple((eachTuple[0], videoBindInfoTuple(*(eachTuple[1:]))) for eachTuple in cursor.fetchall())


def getAllUnBindedVideos() -> Tuple[videoBaseInfoTuple, ...]:
    '''videoBaseInfoTuple: [0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video WHERE hash NOT IN (SELECT hash FROM Binding)")
            return tuple(videoBaseInfoTuple._make(eachTuple[:5]) for eachTuple in cursor.fetchall())


def getBindingFromDB(hash: str) -> Optional[videoBindInfoTuple]:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Binding WHERE hash=?", (hash,))
            return cursor.fetchone()


def getLastWatchTime(hash: str) -> int:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT lastWatchTime FROM Video WHERE hash=?", (hash,))
            return cursor.fetchone()[0]


# time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(1657941885))
def updateLastWatchTime(hash: str, lastWatchTime: int = time.time().__ceil__()) -> None:
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("UPDATE Video SET lastWatchTime=? WHERE hash=?", (lastWatchTime, hash))
            connection.commit()

