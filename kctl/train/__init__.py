import click


@click.group()
@click.option('-b', '--base_image', default='koursaros-base')
@click.pass_context
def train(path_manager, base_image):
    """Save current directory's pipeline"""
    print(base_image)