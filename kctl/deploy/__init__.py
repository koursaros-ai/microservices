
from koursaros.yamls import YamlType, Yaml
from koursaros.utils.misc import subproc
from functools import partial
from threading import Thread
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

    threads = []
    t = Thread(target=ctx.invoke, args=[streamers])
    t.start()
    threads += [t]

    pipeline_yaml = Yaml(app_manager.get_yaml_path(pipeline_name, YamlType.PIPELINE))

    for service_name in pipeline_yaml.services:
        cb = partial(ctx.invoke, service, service_name)
        t = Thread(target=ctx.invoke, args=[service, service_name])
        t.start()

    for t in threads:
        t.join()


@deploy.command()
@click.argument('pipeline_name')
@click.pass_obj
def streamers(app_manager, pipeline_name):
    """Deploy streamers for specified pipeline"""
    pipeline_yaml_path = app_manager.get_yaml_path(pipeline_name, YamlType.PIPELINE)
    pipeline_yaml = Yaml(pipeline_yaml_path)

    cmds = []
    service_names = iter(pipeline_yaml.services)
    first_service = next(service_names)
    service_in = first_service
    while service_names:
        cmd = []
        try:
            service_out = next(service_names)
            cmd = [sys.executable, '-m', 'koursaros.streamer', service_in, service_out]
        except StopIteration:
            # last service's streamer sends back to the first service
            cmd = [sys.executable, '-m', 'koursaros.streamer', service_in, first_service]
        finally:
            cmds += [cmd]

    print(cmds)
    # subproc(cmds)


@deploy.command()
@click.argument('service_name')
@click.option('-a', '--all')
@click.pass_obj
def service(app_manager, service_name, a):
    """Deploy a service"""
    service_yaml_path = app_manager.get_yaml_path(service_name, YamlType.SERVICE)
    service_yaml = Yaml(service_yaml_path)

    if app_manager.is_in_app_path(service_yaml.base, YamlType.BASE):
        app_manager.save_base_to_pkg(service_yaml.base)
    print('Done')
    # cmd = [sys.executable, '-m', 'koursaros.bases.%s' % service_yaml.base, service_yaml_path]
    # subproc(cmd)

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
