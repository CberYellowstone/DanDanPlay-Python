import os
SELF_PATH = os.path.abspath(os.path.dirname(__file__))

FFMPEG_PATH = 'ffmpeg'
FFPROBE_PATH = 'ffprobe'

DB_PATH = 'ddppy.sqlite'

#弹幕存放文件夹，相对于本文件所在文件夹的路径
DANMU_PATH = 'danmu'




#-----以下部分请勿更改-----#
DB_PATH = os.path.join(SELF_PATH, DB_PATH)
DANMU_PATH = os.path.join(SELF_PATH, DANMU_PATH)