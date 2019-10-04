from .checks import check_rabbitmq
from .rabbitmq import bind_rabbitmq
from kctl.utils import BOLD, cls
from subprocess import Popen
import signal
import sys
import os
import click
from ..save import save


@click.group()
@click.option('-c', '--connection', required=True)
@click.option('-r', '--rebind', is_flag=True)
@click.pass_context
def deploy(ctx, connection, rebind):
    """Check configuration yamls, bind rabbitmq, and deploy"""
    path_manager = ctx.obj
    ctx.forward(save)
    check_rabbitmq(connection)
    if rebind:
        bind_rabbitmq(connection)
    os.chdir(path_manager.pipe_root + '..')


@deploy.command()
@click.pass_obj
def pipeline(path_manager):
    pm = path_manager
    from koursaros import pipelines
    pipe = getattr(pipelines, pm.pipe_name)
    services = [cls(service) for service in pipe.Services]
    subproc_servs(path_manager, services)


@deploy.command()
@click.argument('service')
@click.pass_obj
def service(path_manager, service):
    subproc_servs(path_manager, [service])


def subproc_servs(pm, services):
    processes = []

    try:
        for service in services:
            cmd = [sys.executable, '-m', f'{pm.pipe_name}.services.{service}']
            cmd += sys.argv[1:]

            print(f'''Running "{BOLD.format(' '.join(cmd))}"...''')
            p = Popen(cmd)

            processes.append((p, service))

        for p, service in processes:
            p.communicate()

    except KeyboardInterrupt:
        pass

    finally:
        for p, service in processes:

            if p.poll() is None:
                os.kill(p.pid, signal.SIGTERM)
                print(f'Killing pid {p.pid}: {service}')
            else:
                print(f'Process {p.pid}: "{service}" ended...')


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