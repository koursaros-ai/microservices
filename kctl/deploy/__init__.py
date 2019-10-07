from koursaros import Type, Yaml
from grpc_tools import protoc
from typing import List
from pathlib import Path
import random
import click
import sys

MIN_PORT = 49152
MAX_PORT = 65536


def get_random_ports(num_ports: int) -> List[int]:
    return random.sample(range(MIN_PORT, MAX_PORT), num_ports)


def compile_messages_proto(path):
    print(f'Compiling messages for {path}')

    protoc.main((
        '',
        f'-I={path}',
        f'--python_out={path}',
        f'{path}/messages.proto',
    ))


@click.group()
@click.argument('pipeline_yaml_filename')
@click.pass_context
def deploy(ctx):
    """Deploy a pipeline or service"""


@click.command()
@click.argument('pipeline_yaml_filename')
@click.pass_obj
def pipeline(app_manager, pipeline_yaml_filename):
    """Deploy a pipeline yaml"""
    pipeline_name = Path(pipeline_yaml_filename).stem
    build(app_manager, pipeline_yaml_filename)
    build_yaml = app_manager.search_for_yaml(pipeline_name, Type.BUILD)


def build(app_manager, pipeline_yaml_filename):
    """
    Receives a pipeline yaml path and creates a build yaml.
    Saves the build yaml with the pipeline name.
    """

    # find pipeline
    pipeline_name = pipeline_yaml_filename.stem
    pipeline_yaml = app_manager.search_for_yaml(pipeline_name, Type.PIPELINE)

    # assign n * 2 ports for the routers
    number_of_services = len(pipeline_yaml.services)
    ports = iter(get_random_ports(number_of_services * 2))
    current_port = next(ports)

    # assign build yaml location
    build_yaml_dir = app_manager.root.joinpath('build')
    build_yaml_dir.mkdir(exist_ok=True)
    build_yaml_path = build_yaml_dir.joinpath(pipeline_yaml_filename)

    for service_name in pipeline_yaml.services:

        # find each service
        service_yaml_path = app_manager.search_for_yaml_path(service_name, Type.SERVICE)
        service_yaml = Yaml(service_yaml_path)

        # find respective base
        base_yaml_path = app_manager.search_for_yaml_path(service_yaml.base, Type.BASE)
        base_yaml = Yaml(base_yaml_path)

        # validate service yaml with base schema
        app_manager.validate_yaml(service_yaml, base_yaml)

        port_in = current_port
        port_out = next(ports)
        entrypoint = 'kctl deploy service {} {}'.format(service_yaml.base, build_yaml_path)


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