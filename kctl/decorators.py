from .utils import decorator_group
import click
from ipaddress import ip_address

pipeline_options = decorator_group([
    click.argument('pipeline_name'),
    click.argument('runtime')
])

client_options = decorator_group([
    pipeline_options,
    click.option('-c', '--creds'),
])
