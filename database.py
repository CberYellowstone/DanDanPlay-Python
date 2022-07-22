import os
import sqlite3
import time
from contextlib import closing
from typing import Optional, Sequence, Tuple

# from var_dump import var_dump
from config import CONFIG
from unit import videoBaseInfoTuple, videoBindInfoTuple


def initDB():
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS Video (hash TEXT PRIMARY KEY, fileName TEXT, filePath TEXT, fileSize TEXT, videoDuration TEXT, lastWatchTime INTEGER DEFAULT -1)")
            cursor.execute("CREATE TABLE IF NOT EXISTS Binding (hash TEXT PRIMARY KEY, animeId INTEGER, episodeId INTEGER, animeTitle TEXT, episodeTitle TEXT, type TEXT, typeDescription TEXT)")
            cursor.execute("CREATE TABLE IF NOT EXISTS Auth (username TEXT PRIMARY KEY, password TEXT)")
            connection.commit()


def clearDB(part: str = 'all') -> None:
    '''part: 'all' or 'video' or 'binding'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            if part in {'all', 'video'}:
                cursor.execute("DELETE FROM Video")
            if part in {'all', 'binding'}:
                cursor.execute("DELETE FROM Binding")
            connection.commit()


def addVideoIntoDB(hash: str, fileName: str, filePath: str, fileSize: str, videoDuration: str) -> None:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT OR IGNORE INTO Video(hash, fileName, filePath, fileSize, videoDuration) VALUES (?, ?, ?, ?, ?)", (hash, fileName, filePath, fileSize, videoDuration))
            connection.commit()


def addVideosIntoDB(videos: Sequence[Tuple[str, str, str, str, str]]) -> None:
    '''eachTuple: [0] hash: str, [1] fileName: str, [2] filePath: str, [3] fileSize: str, [4] videoDuration: str'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            for video in videos:
                cursor.execute("INSERT OR IGNORE INTO Video(hash, fileName, filePath, fileSize, videoDuration) VALUES (?, ?, ?, ?, ?)", video)
            connection.commit()


def addBindingIntoDB(hash: str, _videoBindInfoTuple: videoBindInfoTuple) -> None:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT OR IGNORE INTO Binding VALUES (?, ?, ?, ?, ?, ?, ?)", (hash, *_videoBindInfoTuple[:6]))
            connection.commit()


def addBindingsIntoDB(bindings: Sequence[Tuple[str, videoBindInfoTuple]]) -> None:
    '''eachTuple: [0] hash, [1] videoBindInfoTuple'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            for binding in bindings:
                cursor.execute("INSERT OR IGNORE INTO Binding VALUES (?, ?, ?, ?, ?, ?, ?)", (binding[0], *(binding[1][:6])))
            connection.commit()


def getVideoFromDB(hash: str) -> Optional[videoBaseInfoTuple]:
    '''videoBindInfoTuple: [0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video WHERE hash=?", (hash,))
            _fetch = cursor.fetchone()
            return videoBaseInfoTuple._make(_fetch[:5]) if _fetch is not None else None


def getAllVideos() -> Tuple[videoBaseInfoTuple, ...]:
    '''videoBindInfoTuple: [0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video")
            return tuple(videoBaseInfoTuple._make(eachTuple[:5]) for eachTuple in cursor.fetchall())


def checkIfVideoBinded(hash: str) -> bool:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Binding WHERE hash=?", (hash,))
            return cursor.fetchone() is None


def getAllBindedVideos() -> Tuple[Tuple[videoBaseInfoTuple, videoBindInfoTuple, int], ...]:
    '''Return: [0] videoBaseInfoTuple, [1] videoBindInfoTuple, [2] lastWatchTime'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video JOIN Binding Using(hash)")
            return tuple((videoBaseInfoTuple(*eachTuple[:5]), videoBindInfoTuple(*eachTuple[-6:]), eachTuple[5]) for eachTuple in cursor.fetchall())


def getSpecificAnimeBindedVideos(animeId: int) -> Tuple[Tuple[videoBaseInfoTuple, videoBindInfoTuple, int], ...]:
    '''Return: [0] videoBaseInfoTuple, [1] videoBindInfoTuple, [2] lastWatchTime'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video JOIN Binding Using(hash) WHERE animeId=?", (animeId,))
            _fetch = cursor.fetchall()
            if _fetch is None:
                return ()
            return tuple((videoBaseInfoTuple(*eachTuple[:5]), videoBindInfoTuple(*eachTuple[-6:]), eachTuple[5]) for eachTuple in _fetch)


def getSpecificEpisodeBindedVideos(episodeId: int) -> Tuple[Tuple[videoBaseInfoTuple, videoBindInfoTuple, int], ...]:
    '''Return: [0] videoBaseInfoTuple, [1] videoBindInfoTuple, [2] lastWatchTime'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video JOIN Binding Using(hash) WHERE episodeId=?", (episodeId,))
            _fetch = cursor.fetchall()
            if _fetch is None:
                return ()
            return tuple((videoBaseInfoTuple(*eachTuple[:5]), videoBindInfoTuple(*eachTuple[-6:]), eachTuple[5]) for eachTuple in _fetch)


def getSpecificBindedVideo(hash: str) -> Tuple[Tuple[videoBaseInfoTuple, videoBindInfoTuple, int]]:
    '''Return: [0] videoBaseInfoTuple, [1] videoBindInfoTuple, [2] lastWatchTime'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video JOIN Binding Using(hash) WHERE hash=?", (hash,))
            _fetch = cursor.fetchone()
            if _fetch is None:
                return ()# type: ignore
            return (videoBaseInfoTuple(*_fetch[:5]), videoBindInfoTuple(*_fetch[-6:]), _fetch[5]),



def getAllUnBindedVideos() -> Tuple[videoBaseInfoTuple, ...]:
    '''videoBaseInfoTuple: [0] hash, [1] fileName, [2] filePath, [3] fileSize, [4] videoDuration'''
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Video WHERE hash NOT IN (SELECT hash FROM Binding)")
            return tuple(videoBaseInfoTuple._make(eachTuple[:5]) for eachTuple in cursor.fetchall())


def getBindingFromDB(hash: str) -> Optional[videoBindInfoTuple]:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Binding WHERE hash=?", (hash,))
            _fetch = cursor.fetchone()
            return videoBindInfoTuple(*_fetch[1:]) if _fetch is not None else None


def getLastWatchTime(hash: str) -> int:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT lastWatchTime FROM Video WHERE hash=?", (hash,))
            return cursor.fetchone()[0] if cursor.fetchone() is not None else -1


# time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(1657941885))
def updateLastWatchTime(hash: str, lastWatchTime: int = time.time().__ceil__()) -> None:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("UPDATE Video SET lastWatchTime=? WHERE hash=?", (lastWatchTime, hash))
            connection.commit()


def clearBrokenVideo() -> Tuple[videoBaseInfoTuple, ...]:
    broken_videoBaseInfoTuples = tuple(eachTuple for eachTuple in getAllVideos() if not os.path.exists(eachTuple.filePath))
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            for broken_videoBaseInfoTuples in broken_videoBaseInfoTuples:
                cursor.execute("DELETE FROM Video WHERE hash=?", (broken_videoBaseInfoTuples.hash,))
                cursor.execute("DELETE FROM Binding WHERE hash=?", (broken_videoBaseInfoTuples.hash,))
                cursor.execute("DELETE FROM Binding WHERE Binding.hash NOT IN (SELECT Video.hash FROM Video)", (broken_videoBaseInfoTuples.hash,))
            connection.commit()
    return broken_videoBaseInfoTuples


def vaildUserIfExists(user: str) -> bool:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Auth WHERE username=?", (user,))
            return cursor.fetchone() is not None


def vaildPassword(user: str, password: str) -> bool:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM Auth WHERE username=? AND password=?", (user, password))
            return cursor.fetchone() is not None


def regUser(user: str, password: str) -> None:
    with closing(sqlite3.connect(CONFIG.DB_PATH)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute("INSERT INTO Auth VALUES (?, ?)", (user, password))
            connection.commit()
