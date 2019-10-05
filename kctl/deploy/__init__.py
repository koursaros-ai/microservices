from .checks import check_rabbitmq
from .rabbitmq import bind_rabbitmq
from ..utils import BOLD, cls, decorator_group
from subprocess import Popen
import signal
import sys
import os
import click
from ..save import save

deploy_options = decorator_group([
    click.option('-c', '--connection', required=True),
    click.option('-r', '--rebind', is_flag=True),
    click.option('-d', '--debug', is_flag=True),
    click.pass_obj
])


@click.group()
@click.pass_context
def deploy(ctx):
    """Check configuration yamls, bind rabbitmq, and deploy"""
    ctx.invoke(save)


@deploy.command()
@deploy_options
def pipeline(pm, connection, rebind, debug):
    """Deploy a pipeline"""
    rmq_setup(pm, connection, rebind)
    services = [cls(service) for service in pm.pipe.Services]
    cmds = []
    for service in services:
        cmd = [
            sys.executable, '-m',
            f'{pm.pipe_name}.services.{service}',
            connection, service,
            'debug' if debug else ''
        ]
        directory = pm.pipe_root + '..'
        cmds.append((directory, cmd))
    subproc(cmds)

@deploy.command()
@click.argument('service')
@deploy_options
def service(pm, service, connection, rebind, debug):
    """Deploy a service or group of services"""
    import pdb; pdb.set_trace()
    rmq_setup(pm, connection, rebind)
    directory = pm.pipe_root + '..'


def rmq_setup(pm, connection, rebind):
    check_rabbitmq(pm, connection)
    if rebind:
        bind_rabbitmq(pm, connection)


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