import click


@click.group()
@click.option('-b', '--base_image', default='koursaros-base')
@click.pass_context
def train(path_manager, ):
    """Save current directory's pipeline"""
    pass