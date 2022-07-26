import itertools
import os
import secrets
from shutil import which
from typing import Any, Optional, Tuple

import click
import yaml
from var_dump import var_dump

from .unit import AbsPath

from .__version__ import VERSION as _VERSION

CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'DanDanPlay-Python', 'config.yml')


_default_configs = {
    'FFMPEG_PATH': ('/usr/bin/ffmpeg' if which('ffmpeg') is None else which('ffmpeg'), '`ffmpeg`可执行文件绝对路径'),
    'DATA_PATH': ('/var/DanDanPlay-Python', '数据存放根路径，绝对路径'),
    'DB_PATH': ('ddppy.sqlite', '数据库路径，相对于数据根路径'),
    'DANMU_PATH': ('danmu', '弹幕文件存放路径，相对于数据根路径'),
    'THUMBNAIL_PATH': ('thumbnail', '缩略图存放路径，相对于数据根路径'),
    'DANMU_DOWNLOAD_THREAD_NUM': (8, '弹幕下载使用线程数，若为1则禁用多线程'),
    'DANMU_INSTANT_GET': (True, '弹幕不存在时是否即时获取'),
    'PUSH_VIDEO_THREAD_NUM': (4, '视频入库使用线程数，若为1则禁用多线程'),
    'MATCH_VIDEO_THREAD_NUM': (4, '视频匹配使用线程数，若为1则禁用多线程'),
    'MATCH_VIDEO_SPLIT_NUM': (12, '匹配视频写入数据库合并数，若为1则不合并写入（推荐为匹配线程的3~4倍左右）'),
    'THUMBNAIL_ENABLE_WEBP': (True, '缩略图是否使用WebP格式，否则使用JPEG格式'),
    'THUMBNAIL_THREAD_NUM': (1, '缩略图创建使用线程数，若为1则禁用多线程'),
    'THUMBNAIL_INSTANT_CREATE': (True, '缩略图不存在时是否即时创建'),
    'API_TOKEN_REQUIRED': (False, 'API访问是否需要密钥')
}

class ConfigNum(click.ParamType):
    name = 'ConfigNum'

    def __init__(self) -> None:
        super().__init__()

    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        if not any((value.isdigit(), value == '-1')):
            self.fail('输入有误，请重试')
        if not int(value) in range(-1, len(_default_configs)+1):
            self.fail(f'序号超出范围，请输入0-{len(_default_configs)-1}', param, ctx)
        value = int(value)
        return super().convert(value, param, ctx)


class Config():
    FFMPEG_PATH: str
    DB_PATH: str
    DATA_PATH: str
    DANMU_PATH: str
    THUMBNAIL_PATH: str
    ONCE_SECRET: str
    API_TOKEN: str
    VERSION: str = _VERSION
    DANMU_DOWNLOAD_THREAD_NUM: int
    PUSH_VIDEO_THREAD_NUM: int
    MATCH_VIDEO_THREAD_NUM: int
    MATCH_VIDEO_SPLIT_NUM: int
    THUMBNAIL_THREAD_NUM: int
    DANMU_INSTANT_GET: bool
    THUMBNAIL_ENABLE_WEBP: bool
    THUMBNAIL_INSTANT_CREATE: bool
    API_TOKEN_REQUIRED: bool

    _config: dict = {}

    def __init__(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, 'r') as c:
                self._config = yaml.safe_load(c)
        except FileNotFoundError:
            if os.environ.get('INITING', 'False') == 'True':
                return
            click.echo(f'找不到{CONFIG_PATH}，请先运行 `cli.py init` 进行初始化。\n', err=True)
            exit(1)
        for i, j in self._config.items():
            setattr(self, i, j)
        if os.environ.get('INITING', 'False') == 'True':
            return
        self.echoCheck()
        self.process()
        self.vaild()

    def process(self):
        self.SELF_PATH = os.path.abspath(os.path.dirname(__file__))
        self.DB_PATH = os.path.join(self.DATA_PATH, self.DB_PATH)
        self.DANMU_PATH = os.path.join(self.DATA_PATH, self.DANMU_PATH)
        self.THUMBNAIL_PATH = os.path.join(self.DATA_PATH, self.THUMBNAIL_PATH)
        self.THUMBNAIL_SUFFIX = '.webp' if self.THUMBNAIL_ENABLE_WEBP else '.jpg'
        self.THUMBNAIL_FORMAT = 'webp' if self.THUMBNAIL_ENABLE_WEBP else 'mjpeg'
        self.ONCE_SECRET = secrets.token_hex(32)

    def vaild(self):
        # 检查值是否合法
        assert os.path.isabs(self.DATA_PATH), 'DATA_PATH 必须为绝对路径'
        assert self.DANMU_DOWNLOAD_THREAD_NUM >= 1, '`DANMU_DOWNLOAD_THREAD_NUM` 至少为 1'
        assert isinstance(self.THUMBNAIL_ENABLE_WEBP, bool), '`THUMBNAIL_ENABLE_WEBP` 必须是布尔值'
        assert self.THUMBNAIL_THREAD_NUM >= 1, '`THUMBNAIL_THREAD_NUM` 至少为 1'

    def implicitCheck(self) -> Tuple[bool, str]:
        # 检查配置是否齐全
        _difference = tuple(c for c in _default_configs if c not in set(self._config))
        if not len(_difference) == 0:
            return False, '配置缺失：\n' + '、 '.join(_difference) + '请运行 `cli.py init` 重新进行初始化。\n'
        if self._config['API_TOKEN_REQUIRED'] and self._config.get('API_TOKEN', None) is None and os.environ.get('CONFIGING', 'False') != 'True':
            return False, 'API访问密钥缺失，请运行 `cli.py config` 进行设置。\n'
        return True, ''

    def echoCheck(self):
        state, message = self.implicitCheck()
        if not state:
            click.echo(message=message, err=True)
            exit(1)

    def reload(self):
        self.__init__()

    def dump(self):
        with open(CONFIG_PATH, 'w') as c:
            yaml.safe_dump(self._config, c, default_flow_style=False)

    def new(self, _dict: dict):
        self._config.update(_dict)
        self.dump()
        self.reload()

    def edit(self):
        api_token = ('API_TOKEN', (self._config.get('API_TOKEN', None), 'API访问密钥'))
        # var_dump(list(enumerate(_default_configs.items()))); var_dump(api_token);exit()
        click.echo('\n'.join(f"{n} - {j[1][1].split('，')[0]}：{self._config[j[0]]}" for n, j in (*enumerate(_default_configs.items()), (len(_default_configs), api_token))) + '\n')
        num = click.prompt('请输入配置项前的编号进行选择，输入-1退出', default=-1, show_default=False, value_proc=ConfigNum())
        click.clear()
        if num == -1:
            click.echo('已退出配置！')
            return
        _items = (*_default_configs.items(), api_token)
        value = click.prompt(_items[num][1][1], default=_items[num][1][0], type=AbsPath() if os.path.isabs(f'{_items[num][1][0]}') else None)
        self._config[_items[num][0]] = value
        self.dump()
        self.reload()
        click.echo(f'{_items[num][0]} 已更新为：{self._config[_items[num][0]]}')
        os.environ['CONFIGING'] = 'False'



if __name__ == 'DanDanPlayPython.config':
    CONFIG = Config()
