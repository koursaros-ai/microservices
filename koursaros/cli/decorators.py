from .utils import decorator_group
import click

pipeline_options = decorator_group([
    click.argument('flow_name'),
    click.option('-r', '--runtime', required=True),
    click.pass_obj
])

client_options = decorator_group([
    pipeline_options,
    click.option('-c', '--creds'),
])
