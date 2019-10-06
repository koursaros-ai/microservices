import click
from koursaros.utils.misc import subproc

@click.command()
@click.argument('name')
@click.pass_obj
def train(pathmanager, name):
    subproc([('./', 'python -m koursaros.train %s' % name)])

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    pass
