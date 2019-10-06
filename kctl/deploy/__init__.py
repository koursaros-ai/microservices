from koursaros import Type, Yaml
from grpc_tools import protoc
from pathlib import Path
import click
import sys


def compile_messages_proto(path):
    print(f'Compiling messages for {path}')

    protoc.main((
        '',
        f'-I={path}',
        f'--python_out={path}',
        f'{path}/messages.proto',
    ))


@click.command()
@click.argument('pipeline_yaml_name')
@click.pass_obj
def deploy(app_manager, pipeline_yaml_filename):
    """Deploy a pipeline yaml"""
    pipeline_name = Path(pipeline_yaml_filename).stem
    build(app_manager, pipeline_name)
    build_yaml = app_manager.search_for_yaml(pipeline_name, Type.BUILD)
    print(build_yaml)


def build(app_manager, pipeline_name):
    """
    Receives a pipeline yaml path and creates a build yaml.
    Saves the build yaml with the pipeline name.
    """

    # find pipeline
    pipeline_yaml = app_manager.search_for_yaml(pipeline_name, Type.PIPELINE)

    for service_name in pipeline_yaml.services:

        # find each service
        service_yaml = Yaml(app_manager.search_for_yaml_path(service_name, Type.SERVICE))

        # find respective base
        base_yaml_path = app_manager.search_for_yaml_path(service_yaml.base, Type.BASE)
        base_yaml = Yaml(base_yaml_path)

        # validate service yaml with base schema
        app_manager.validate_yaml(service_yaml, base_yaml)

        entrypoint = '{}{}{}{}'.format(
            sys.executable, '-m', base_yaml_path.parent, pipeline_yaml.__path__)


        # compile messages for that service
        # compile_messages_proto(service_path)

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