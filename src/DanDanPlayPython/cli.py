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
    '''运行 API 服务，可选参数：--host（默认为0.0.0.0），--port（默认为5000）'''
    from .app import run as _run
    _run(host, port)


@CLI.command()
def config():
    '''更改配置项'''
    os.environ['CONFIGING'] = 'True'
    from .config import CONFIG
    CONFIG.edit()


@CLI.command()
@click.argument('path')
@click.option('--show-faild', 'show_faild', flag_value=True)
@click.option('--silent', 'silent', flag_value=True)
def add(path: str, show_faild:bool = False, silent:bool = False):
    '''向数据库中增加视频，参数：Path（可为单文件路径或目录路径），可选参数：--show-faild（展示失败项）、--silent（静默输出）'''
    from .video import pushVideoBaseInfo2DB
    from .database import getAllVideos
    bf = len(getAllVideos())
    is_dir = os.path.isdir(path)
    state, faileds = pushVideoBaseInfo2DB(path, show_progress=((not silent) and is_dir), is_dir=is_dir)
    success = len(getAllVideos()) - bf
    if silent:
        return
    click.echo(f'\n本次成功添加 {success} 个视频，' + ('无失败项目。' if state else f'其中跳过 {len(faileds)} 个。\n') + ('' if show_faild else '\n若要查看跳过项目，请附带 --show-faild'))
    if show_faild:
        click.echo('跳过的项目：\n'+'\n'.join(faileds)+'\n')



if __name__ == '__main__':
    CLI()
