import os

import click


@click.group()
@click.help_option("--help", "-h")
@click.version_option("--version", "-v", "-V", message=
'''DanDanPlay-Python，当前版本：%(version)s

项目主页：https://github.com/CberYellowstone/DanDanPlay-Python
问题报告：https://github.com/CberYellowstone/DanDanPlay-Python/issues
''')
def CLI():
    pass

@CLI.command()
def init():
    '''执行初始化操作'''
    os.environ['INITING'] = 'True'
    from .init import init as _init
    _init()

@CLI.command()
@click.option('--host', '-h', default='0.0.0.0', help='监听地址')
@click.option('--port', '-p', default=5000, help='监听端口')
def run(host, port):
    '''运行 API 服务， 可选参数：--host（默认为0.0.0.0），--port（默认为5000）'''
    from .app import run as _run
    _run(host, port)

@CLI.command()
def config():
    '''更改配置项'''
    os.environ['CONFIGING'] = 'True'
    from .config import CONFIG
    CONFIG.edit()


if __name__ == '__main__':
    CLI()
