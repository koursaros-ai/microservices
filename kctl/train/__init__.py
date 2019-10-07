import click
import sys


@click.command()
@click.argument('name')
@click.pass_obj
def train(app_manager, name):
    cmd = [sys.executable, '-m', 'koursaros.trainer',  name]
    app_manager.subproc(cmd)


@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    pass
