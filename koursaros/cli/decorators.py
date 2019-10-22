from .utils import decorator_group
import click

pipeline_options = decorator_group([
    click.argument('pipeline_name'),
    click.option('-r', '--runtime', required=True),
    click.option('-y', '--yes', is_flag=True),
    click.pass_obj
])

client_options = decorator_group([
    pipeline_options,
    click.option('-c', '--creds'),
    click.pass_obj
])
