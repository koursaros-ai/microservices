

import click
from .compile import PipelineBottle
from importlib import reload


@click.command()
@click.pass_obj
def save(path_manager):
    """Save current directory's pipeline"""
    bottle = PipelineBottle(path_manager)

    if bottle.cached():
        print(f'No changes to "{bottle.pipe_name}", skipping compile...')
    else:
        print(f'Compiling pipeline "{bottle.pipe_name}"...')
        bottle.compile_connections()
        bottle.compile_services()
        bottle.compile_messages()
        bottle.save()
        reload(path_manager.pipelines)


