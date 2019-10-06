from koursaros import Ktype, Yaml
from grpc_tools import protoc
from subprocess import Popen
from ..utils import BOLD
import signal
import click
import sys
import os


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
def deploy(app_manager, pipeline_yaml_name):
    """Deploy a pipeline yaml"""
    build(app_manager, pipeline_yaml_name)
    


def build(app_manager, pipeline_yaml_name):
    """Receives a pipeline yaml path and creates a build yaml"""

    # find pipeline
    pipeline_path, pipeline_yaml_path = app_manager.search_for_type(
        pipeline_yaml_name, Ktype.PIPELINE)
    pipeline_yaml = Yaml(pipeline_yaml_path)

    for service_name in pipeline_yaml.services:

        # find each service
        service_path, service_yaml_path = app_manager.search_for_type(
            service_name, Ktype.SERVICE)
        service_yaml = Yaml(service_yaml_path)

        # find respective base
        base_path, base_yaml_path = app_manager.search_for_type(
            service_yaml.base, Ktype.BASE)
        base_yaml = Yaml(base_yaml_path)

        # validate service yaml with base schema
        app_manager.validate_yaml(service_yaml, base_yaml)

        entrypoint = '{}{}{}{}'.format(
            sys.executable, '-m',
            service_yaml_path,
            pipeline_yaml.__path__
        )


        # compile messages for that service
        # compile_messages_proto(service_path)



def subproc(cmds):
    """Subprocess a list of commands from specified
     directories and cleanup procs when done

    :param cmds: iterable list of tuples (directory: cmd)
    """
    procs = []

    try:
        for path, cmd in cmds:
            os.chdir(path)
            formatted = BOLD.format(' '.join(cmd))

            print(f'''Running "{formatted}" from "{path}"...''')
            p = Popen(cmd)
            procs.append((p, formatted))

        for p, formatted in procs:
            p.communicate()

    except KeyboardInterrupt:
        pass

    finally:
        for p, formatted in procs:

            if p.poll() is None:
                os.kill(p.pid, signal.SIGTERM)
                print(f'Killing pid {p.pid}: {formatted}')
            else:
                print(f'Process {p.pid}: "{formatted}" ended...')


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