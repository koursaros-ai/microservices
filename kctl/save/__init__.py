import click
from .compile import PipelineBottler


IMPORTS = ['from .messages_pb2 import *', 'from koursaros.base import *']


@click.command()
@click.pass_obj
def save(path_manager):
    """Save current directory's pipeline"""
    bottle = PipelineBottler(path_manager)

    if bottle.cached():
        print(f'No changes to "{bottle.pm.pipe_name}", skipping compile...')
    else:
        print(f'Compiling pipeline "{bottle.pm.pipe_name}"...')
        bottle.compile_connections()
        bottle.compile_services()
        bottle.compile_messages()
        bottle.add_headers(IMPORTS)
        bottle.save()
        path_manager.reload()


