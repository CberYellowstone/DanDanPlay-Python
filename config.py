# ffmpeg可执行文件绝对路径
FFMPEG_PATH = 'ffmpeg'

DB_PATH = 'ddppy.sqlite'

# 数据存放根路径，相对于本文件所在路径
DATA_PATH = 'data'


# 弹幕文件存放路径，相对于数据根路径
DANMU_PATH = 'danmu'

# 弹幕下载使用线程数，若为1则禁用多线程
DANMU_DOWNLOAD_THREAD_NUM = 1


# 匹配视频使用线程数，若为1则禁用多线程
MATCH_VIDEO_THREAD_NUM = 4

# 匹配视频写入数据库合并数，若为1则不合并写入（推荐为匹配线程的3~4倍左右）
MATCH_VIDEO_SPLIT_NUM = 12


# 缩略图存放路径，相对于数据根路径
THUMBNAIL_PATH = 'thumbnail'

# 缩略图是否使用WebP格式，否则使用JPEG格式
THUMBNAIL_ENABLE_WEBP = True

# 缩略图创建使用线程数，若为1则禁用多线程
THUMBNAIL_THREAD_NUM = 1



#-----请勿更改以下部分-----#
import os
SELF_PATH = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(SELF_PATH, DATA_PATH, DB_PATH)
DANMU_PATH = os.path.join(SELF_PATH, DATA_PATH, DANMU_PATH)
THUMBNAIL_PATH = os.path.join(SELF_PATH, DATA_PATH, THUMBNAIL_PATH)
THUMBNAIL_SUFFIX = '.webp' if THUMBNAIL_ENABLE_WEBP else '.jpg'
THUMBNAIL_FORMAT = 'webp' if THUMBNAIL_ENABLE_WEBP else 'mjpeg'

# 检查值是否合法
assert DANMU_DOWNLOAD_THREAD_NUM >= 1, 'DANMU_DOWNLOAD_THREAD_NUM min value must be 1'
assert isinstance(THUMBNAIL_ENABLE_WEBP, bool), 'THUMBNAIL_ENABLE_WEBP must be bool'
assert THUMBNAIL_THREAD_NUM >= 1, 'THUMBNAIL_THREAD_NUM min value must be 1'