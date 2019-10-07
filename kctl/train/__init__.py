import click
from koursaros.utils.misc import subproc
import sys
import os

@click.command()
@click.argument('name')
@click.pass_obj
def train(appmanager, name):
    cmd = [sys.executable, '-m', 'koursaros.trainer',  name]
    subproc([cmd])

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    pass
