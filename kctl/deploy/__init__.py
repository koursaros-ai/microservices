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


# @deploy.command()
# @click.pass_obj
# def pipeline(obj):
#     print(obj)
#     raise SystemExit
#     os.chdir(pipe_path + '..')
#     import koursaros.pipelines
#     pipe = getattr(koursaros.pipelines, name)
#     pipe = pipe(None)
#     deploy(pipe.Services, args)
#
#
# @deploy.command()
# @click.argument('name')
# @click.pass_obj
# def service(obj):
#     os.chdir(pipe_path + '..')
#     import koursaros.pipelines
#     pipe = getattr(koursaros.pipelines, name)
#     pipe = pipe(None)
#     service = getattr(pipe.Services, args.service_name)
#     deploy([service], args)

#
# def deploy(services, args):
#     processes = []
#
#     try:
#         for service in services:
#             cmd = [
#                 sys.executable,
#                 '-m',
#                 f'{args.pipeline_name}.services.{cls(service)}'
#             ] + sys.argv[1:]
#
#             print(f'''Running "{BOLD.format(' '.join(cmd))}"...''')
#             p = Popen(cmd)
#
#             processes.append((p, cls(service)))
#
#         for p, service_cls in processes:
#             p.communicate()
#
#     except KeyboardInterrupt:
#         pass
#     except Exception as exc:
#         print(exc)
#
#     finally:
#         for p, service_cls in processes:
#
#             if p.poll() is None:
#                 os.kill(p.pid, signal.SIGTERM)
#                 print(f'Killing pid {p.pid}: {service_cls}')
#             else:
#                 print(f'process {p.pid}: "{service_cls}" ended...')
