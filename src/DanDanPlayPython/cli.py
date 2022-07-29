import os
from typing import Any, Optional, Sequence, Tuple

import click
from var_dump import var_dump


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
    '''向数据库中增加视频，参数：Path（可为单文件路径或目录路径），可选参数：--show-faild、--silent'''
    from .video import pushVideoBaseInfo2DB
    from .database import getAllVideos
    bf = len(getAllVideos())
    is_dir = os.path.isdir(path)
    state, faileds = pushVideoBaseInfo2DB(path, show_progress=((not silent) and is_dir), is_dir=is_dir)
    succeed = len(getAllVideos()) - bf
    if silent:
        return
    click.echo(f'\n本次成功添加 {succeed} 个视频，' + ('无失败项目。' if state else f'其中跳过 {len(faileds)} 个。') + ('' if show_faild else '\n若要查看跳过项目，请附带 --show-faild'))
    if show_faild:
        click.echo('跳过的项目：\n'+'\n'.join(faileds)+'\n')


class SN(click.ParamType):
    name = 'SN'
    def __init__(self, scope: int, letter: Sequence[str]) -> None:
        super().__init__()
        self.scope = scope
        self.letter = letter
    def convert(self, value: Any, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> Any:
        if value in self.letter:
            return super().convert(value, param, ctx)
        if not value.isdigit():
            self.fail('输入有误，请重试')
        if int(value) not in range(self.scope):
            self.fail(f'序号超出范围，请输入0-{self.scope}', param, ctx)
        value = int(value)
        return super().convert(value, param, ctx)

@CLI.command()
@click.option('--silent', 'silent', flag_value=True)
@click.option('-l', 'show_detail', flag_value=True)
@click.option('-m', 'manual', flag_value=True)
def match(silent:bool = False, show_detail:bool = False, manual:bool = False):
    '''使用 DanDanPlay-API 匹配已入库的视频文件，可选参数：-l、-m、--silent'''
    from .dandanplayAPI import bindVideosIfIsMatched, searchDanDanPlay
    from .database import ignoreVideo, addBindingsIntoDB
    from .unit import videoBindInfoTuple, videoBaseInfoTuple
    binded, unbinded = bindVideosIfIsMatched(show_progress=not silent)
    if silent:
        return
    click.echo(f'成功匹配 {len(binded)} 个，{len(unbinded)} 个未匹配。\n' + ('' if show_detail else '\n若要查看详情，请附带 -l'))
    if show_detail and len(unbinded) != 0:
        click.echo_via_pager('以下是未识别的文件：\n' + '\n'.join((f"{base[0].fileName}" for base in unbinded)) + '\n以上是未识别的文件，若要手动匹配请附带 -m\n按 q 退出')
    if manual:
        for n, eachTuple in enumerate(unbinded):
            # eachTuple: Tuple[videoBaseInfoTuple, Tuple[videoBindInfoTuple]]
            click.clear()
            click.echo(f'正在进行手动匹配 {n+1}/{len(unbinded)+1}')
            click.echo(f'未识别的文件 - {n+1}：{os.path.dirname(eachTuple[0].filePath)}\n{eachTuple[0].fileName}\n')
            click.echo('\n'.join((f"{i}：{_eachVideoBindInfoTuple.typeDescription} | 《{_eachVideoBindInfoTuple.animeTitle}》 - {_eachVideoBindInfoTuple.episodeTitle}" for i, _eachVideoBindInfoTuple in enumerate(eachTuple[1]))))
            value = click.prompt(f'请输入序号（0-{len(eachTuple[1])-1}），输入 i 永久忽略，输入 s 自定义搜索', value_proc=SN(len(eachTuple[1]), ('i', 's')))
            if value == 'i':
                ignoreVideo(eachTuple[0].hash)
            if isinstance(value, int):
                addBindingsIntoDB(((eachTuple[0].hash, eachTuple[1][value]),))
            if value == 's':
                while(1):
                    click.clear()
                    click.echo(f'正在进行手动匹配 {n+1}/{len(unbinded)+1}')
                    click.echo(f'未识别的文件 - {n+1}：{os.path.dirname(eachTuple[0].filePath)}\n{eachTuple[0].fileName}\n')
                    hasMore, _videoBindInfoTuples = searchDanDanPlay(click.prompt('正在进行手动搜索，请输入关键词', type=str))
                    if len(_videoBindInfoTuples) >= 15:
                        if hasMore:
                            click.echo(click.style('DanDanPlay API 返回结果集过大，尝试填写更详细的信息以缩小搜索范围\n', fg='yellow'))
                        _animeTitles = tuple({_videoBindInfoTuple.animeTitle for _videoBindInfoTuple in _videoBindInfoTuples})
                        click.echo('\n'.join(f'{i}： 《{_animeTitle}》' for i, _animeTitle in enumerate(_animeTitles)))
                        _value = click.prompt(f'请输入序号（0-{len(_animeTitles)-1}），输入 i 永久忽略，输入 r 重新搜索', value_proc=SN(len(_animeTitles), ('i', 'r')))
                        if _value == 'i':
                            ignoreVideo(eachTuple[0].hash)
                            break
                        if isinstance(_value, int):
                            __videoBindInfoTuples = tuple(_videoBindInfoTuple for _videoBindInfoTuple in _videoBindInfoTuples if _videoBindInfoTuple.animeTitle == _animeTitles[_value])
                            click.echo('\n'.join((f'{i}：《{_videoBindInfoTuple.animeTitle}》 - {_videoBindInfoTuple.episodeTitle}' for i, _videoBindInfoTuple in enumerate(__videoBindInfoTuples))))
                            __value = click.prompt(f'请输入序号（0-{len(__videoBindInfoTuples)-1}），输入 i 永久忽略', value_proc=SN(len(__videoBindInfoTuples), ('i')))
                            if __value == 'i':
                                ignoreVideo(eachTuple[0].hash)
                                break
                            if isinstance(__value, int):
                                addBindingsIntoDB(((eachTuple[0].hash, __videoBindInfoTuples[__value]),))
                                break
                    else:
                        click.echo('\n'.join((f'{i}：《{_videoBindInfoTuple.animeTitle}》 - {_videoBindInfoTuple.episodeTitle}' for i, _videoBindInfoTuple in enumerate(_videoBindInfoTuples))))
                        __value = click.prompt(f'请输入序号（0-{len(_videoBindInfoTuples)-1}），输入 i 永久忽略', value_proc=SN(len(_videoBindInfoTuples), ('i')))
                        if __value == 'i':
                            ignoreVideo(eachTuple[0].hash)
                            break
                        if isinstance(__value, int):
                            addBindingsIntoDB(((eachTuple[0].hash, _videoBindInfoTuples[__value]),))
                            break


@CLI.command()
@click.argument('sub_command')
def db(sub_command):
    '''管理已入库文件，子命令：check、ignore'''
    if sub_command not in ('check', 'ignore'):
        click.echo(click.style(f'子命令 `{sub_command}` 有误，执行 dandanplay-python db --help 以获得帮助', fg='yellow'), err=True)


if __name__ == '__main__':
    CLI()
