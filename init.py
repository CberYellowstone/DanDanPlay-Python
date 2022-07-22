import contextlib
import os
from typing import Any, Optional

from var_dump import var_dump
import click

from config import CONFIG, _default_configs
from database import initDB


def delAll():
    with contextlib.suppress(FileNotFoundError):
        os.remove(CONFIG.DATA_PATH)

class AbsPath(click.ParamType):
    name = 'AbsPath'
    def __init__(self) -> None:
        super().__init__()
    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        if not os.path.isabs(value):
            self.fail('请输入绝对路径', param, ctx)
        return super().convert(value, param, ctx)


def initConfig():
    _user_configs = {}
    for eachConfig in _default_configs.items():
        _user_configs[eachConfig[0]] = click.prompt(eachConfig[1][1], default=eachConfig[1][0], type=AbsPath() if os.path.isabs(f'{eachConfig[1][0]}') else None)
    os.environ['INITING'] = 'False'
    CONFIG.new(_user_configs)


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
