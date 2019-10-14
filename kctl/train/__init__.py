import click
import sys


@click.command()
@click.argument('name')
@click.pass_obj
def train(app_manager, name):
    cmd = [sys.executable, '-m', 'koursaros.trainer',  name]
    app_manager.subproc(cmd)


@click.command()
@click.argument('name')
@click.option('-s', '--source')
@click.option('-d', '--destination')
@click.pass_obj
def predict(app_manager, name, s, d):
    """Save current directory's pipeline"""
    cmd = [sys.executable, '-m', 'koursaros.predictor', name, s, d]
