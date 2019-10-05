from subprocess import Popen
from ..utils import BOLD
import signal
import click
import sys
import os


@click.group()
@click.pass_context
def deploy(ctx):
    """Check configuration yamls, bind rabbitmq, and deploy"""


@deploy.command()
@click.option('name')
def pipeline(pm, name):
    """Deploy a pipeline"""
    cmds = []
    for service in pm.get_pipe_yaml(name):
        deploy_path = pm.get_serv_path(service) + '..'
        cmd = [sys.executable, '-m', service]
        cmds.append((deploy_path, cmd))

    subproc(cmds)


def subproc(cmds):
    """Subprocess a list of commands from specified
     directories and cleanup procs when done

    :param cmds: iterable list of tuples (directory: cmd)
    """
    procs = []

    try:
        for directory, cmd in cmds:
            os.chdir(directory)
            formatted = BOLD.format(' '.join(cmd))

            print(f'''Running "{formatted}" from "{directory}"...''')
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