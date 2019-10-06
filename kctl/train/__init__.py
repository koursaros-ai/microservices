import click

@click.command()
@click.argument('name')
@click.pass_obj
def train(pathmanager, name):
    pass

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    pass
