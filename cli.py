import os
import click

@click.group()
def CLI():
    pass


@CLI.command()
def init():
    os.environ['INITING'] = 'True'
    from init import init as _init
    _init()

@CLI.command()
@click.option('--host', '-h', default='0.0.0.0', help='监听地址')
@click.option('--port', '-p', default=5000, help='监听端口')
def run(host, port):
    from app import run as _run
    _run(host, port)





if __name__ == '__main__':
    CLI()