
from koursaros.yamls import YamlType, Yaml
import click
import sys


@click.group()
@click.pass_context
def deploy(ctx):
    """Deploy a pipeline, service, or streamers"""


@deploy.command()
@click.argument('pipeline_name')
@click.pass_context
def pipeline(ctx, pipeline_name):
    """
    Deploy a pipeline by threading the deployment
    of streamers and each service.
    """
    app_manager = ctx.obj
    app_manager.raise_if_not_app_root()


