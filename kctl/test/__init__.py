from koursaros.yamls import YamlType, Yaml
import click
import sys


@click.group()
@click.pass_context
def test(ctx):
    """Test a running pipeline"""


@test.command()
@click.argument('pipeline_name')
@click.pass_context
def pipeline(ctx, pipeline_name, verbose):
    """
    Deploy a pipeline by threading the deployment
    of streamers and each service.
    """
    app_manager = ctx.obj
    app_manager.raise_if_not_app_root()

    ctx.invoke(router, pipeline_name=pipeline_name)
    ctx.invoke(streamers, pipeline_name=pipeline_name)

    pipeline_yaml = Yaml(app_manager.get_yaml_path(pipeline_name, YamlType.PIPELINE))

    for service_name in pipeline_yaml.services:
        ctx.invoke(service, service_name=service_name)