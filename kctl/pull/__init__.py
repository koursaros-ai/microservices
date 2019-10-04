
import click
from shutil import rmtree, copytree
from subprocess import call


@click.group()
@click.pass_context
def pull(ctx):
    pass


@pull.command()
@click.option('-g', '--git')
@click.option('-d', '--dir')
@click.pass_obj
def pull_pipeline(path_manager, g, d):
    """Pull a pipeline"""
    path_manager.raise_if_pipe_root()
    call(['git', 'clone', g])

    cache_dir = path_manager.pipe_root + '.cache'
    dirname = g.split("/")[-1]

    if d:
        copytree(f'{dirname}/{d}', cache_dir)
        rmtree(dirname)
        copytree(cache_dir, dirname)
        rmtree(cache_dir)