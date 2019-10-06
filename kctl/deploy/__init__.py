from koursaros import Ktype
from grpc_tools import protoc
from subprocess import Popen
from ..utils import BOLD
import signal
import click
import sys
import os


def compile_messages(in_path, out_path):
    print(f'Compiling messages for {in_path}')

    protoc.main((
        '',
        f'-I={in_path}',
        f'--python_out={out_path}',
        f'{in_path}/messages.proto',
    ))


@click.command()
@click.argument('yaml')
@click.pass_obj
def deploy(app_manager, yaml):
    """Deploy a pipeline"""
    import pdb; pdb.set_trace()
    cmds = []
    pipeline_yaml = app_manager.search_yaml(app_manager.base, Ktype.PIPELINE)
    for service in pipeline_yaml.services:
        base_path = app_manager.search_path(service.base, Ktype.BASE)
        os.makedirs(app_manager.root.joinpath, exist_ok=True)
        # compile_messages(serv_path, out_path)

        cmd = [sys.executable, '-m', pipeline_yaml.__path__]
        cmds.append((base_path.joinpath('..'), cmd))

    subproc(cmds)


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