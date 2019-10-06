import click
from koursaros.utils.misc import subproc

@click.command()
@click.argument('name')
@click.pass_obj
def train(appmanager, name):
    subproc([(appmanager.pkg_path, 'python -m koursaros.trainer %s' % name)])

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    pass
