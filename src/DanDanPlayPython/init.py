import contextlib
import os
from shutil import which

import click
from var_dump import var_dump

from .config import CONFIG, _default_configs
from .database import initDB
from .unit import AbsPath


def delAll():
    with contextlib.suppress(FileNotFoundError):
        os.remove(CONFIG.DATA_PATH)


def initConfig():
    if CONFIG.implicitCheck()[0]:
        click.echo('配置已存在，无需初始化。\n')
        exit(0)
    click.echo('正在初始化配置……\n')
    if which('ffmpeg') is None:
        click.echo('未检测到`ffmpeg`，请确认是否安装了`ffmpeg`。')
    _user_configs = {
        eachConfig[0]: click.prompt(
            eachConfig[1][1],
            default=eachConfig[1][0],
            type=AbsPath() if os.path.isabs(f'{eachConfig[1][0]}') else None
        )
        for eachConfig in _default_configs.items()
    }
    _user_configs['API_TOKEN'] = click.prompt('请输入API访问密钥', type=str) if _user_configs['API_TOKEN_REQUIRED'] else None
    os.environ['INITING'] = 'False'
    CONFIG.new(_user_configs)
    click.clear()
    click.echo('成功初始化配置！尝试执行 `dandanplay add <file>` 添加视频吧！')


def initFolder():
    if os.path.exists(CONFIG.DATA_PATH) and not os.path.isdir(CONFIG.DATA_PATH):
        os.replace(CONFIG.DATA_PATH, f'{CONFIG.DATA_PATH}.bak')
    for each_path in CONFIG.DANMU_PATH, CONFIG.THUMBNAIL_PATH:
        if os.path.exists(each_path) and not os.path.isdir(each_path):
            # TODO: Logging
            os.replace(each_path, f'{each_path}.bak')
        with contextlib.suppress(FileExistsError):
            os.makedirs(os.path.join(each_path))

def init():
    initConfig()
    initFolder()
    initDB()

if __name__ == '__main__':
    init()
