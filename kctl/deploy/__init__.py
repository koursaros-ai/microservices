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
@click.pass_context
def deploy(path_manager):
    """Check configuration yamls, bind rabbitmq, and deploy"""
    save(path_manager)


@deploy.command()
@click.option('-c', '--connection', required=True)
@click.option('-r', '--rebind', is_flag=True)
@click.pass_obj
def pipeline(path_manager, connection, rebind):
    check_rabbitmq(connection)
    if rebind:
        bind_rabbitmq(connection)
    pm = path_manager
    os.chdir(pm.pipe_root + '..')
    services = [cls(service) for service in pm.pipe.Services]
    deploy(services)


@deploy.command()
@click.argument('service')
@click.option('-c', '--connection', required=True)
@click.option('-r', '--rebind', is_flag=True)
@click.pass_obj
def service(path_manager, service, connection, rebind):
    check_rabbitmq(connection)
    if rebind:
        bind_rabbitmq(connection)
    pm = path_manager
    os.chdir(pm.pipe_root + '..')
    deploy([service])


def subproc_servs(services, pm):

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