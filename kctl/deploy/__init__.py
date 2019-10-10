
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

    ctx.invoke(router)
    ctx.invoke(streamers, pipeline_name=pipeline_name)

    pipeline_yaml = Yaml(app_manager.get_yaml_path(pipeline_name, YamlType.PIPELINE))

    for service_name in pipeline_yaml.services:
        ctx.invoke(service, pipeline_name=pipeline_name, service_name=service_name)


@deploy.command()
@click.argument('pipeline_name')
@click.pass_obj
def streamers(app_manager, pipeline_name):
    """Deploy streamers for specified pipeline"""
    pipeline_yaml_path = app_manager.get_yaml_path(pipeline_name, YamlType.PIPELINE)
    pipeline_yaml = Yaml(pipeline_yaml_path)

    service_in = 'ROUTER'
    for service_out in pipeline_yaml.services:
        cmd = [sys.executable, '-m', 'koursaros.streamer', service_in, service_out]
        service_in = service_out
        app_manager.subproc(cmd)


@deploy.command()
@click.pass_obj
def router(app_manager):
    """Deploy the router"""
    cmd = [sys.executable, '-m', 'koursaros.router']
    app_manager.subproc(cmd)


@deploy.command()
@click.argument('pipeline_name')
@click.argument('service_name')
@click.pass_obj
def service(app_manager, pipeline_name, service_name):
    """Deploy a service"""
    service_yaml_path = app_manager.get_yaml_path(service_name, YamlType.SERVICE)
    service_yaml = Yaml(service_yaml_path)
    pipe_yaml_path = app_manager.get_yaml_path(pipeline_name, YamlType.PIPELINE)
    base_yaml_path = app_manager.get_yaml_path(service_yaml.base, YamlType.BASE)

    if base_yaml_path is None:
        raise FileNotFoundError('Could not find base "%s" base.yaml' % service_yaml.base)

    if app_manager.is_in_app_path(service_yaml.base, YamlType.BASE)\
            and not app_manager.is_in_root_path(service_yaml.base, YamlType.BASE):
        app_manager.save_base_to_pkg(service_yaml.base)

    cmd = [sys.executable, '-m', 'koursaros.bases.%s' % service_yaml.base,
           str(service_yaml_path), str(pipe_yaml_path)]

    app_manager.subproc(cmd)


# else:
#     from .create import build_trigger
#     from .create import build_cloudbuild
#     from .create import build_deployment
#     from .create import build_dockerfile
#     from .create import git_push
#
#     import uuid
#     tag = str(uuid.uuid4())[:8]
#
#     if pushargs.all:
#         build_trigger(all=True)
#         build_cloudbuild(tag, all=True)
#         build_dockerfile(all=True)
#         build_deployment(tag, all=True)
#         git_push(all=True)
#
#     else:
#         microservices = pushargs.microservices
#         build_trigger(microservices=microservices)
#         build_cloudbuild(tag, microservices=microservices)
#         build_dockerfile(microservices=microservices)
#         build_deployment(tag, microservices=microservices)
#         git_push(microservices=microservices)
