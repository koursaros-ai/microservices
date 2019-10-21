
from ..decorators import *
import docker
import time


@click.group()
def deploy():
    """Deploy gnes services."""


@deploy.command()
def pipeline():
    """Deploy a pipeline with compose or k8s. """


@deploy.command()
@client_options
@click.pass_obj
def client(app_manager, pipeline_name, runtime, creds):
    """Deploy a client with docker. """
    flow = app_manager.get_flow('pipelines', pipeline_name, runtime)
    cn = flow._client_node
    tag = 'gnes-client:%s' % (cn.pop('name'))

    switches = ['--mode', runtime,
                '--creds', creds,
                ] + ['--%s %s' % (k, v) for k, v in cn.items()]

    response = docker.from_env().containers.run(tag, stream=True, command=switches)

    for stream in response:
        app_manager.logger.info(stream)


@pipeline.command()
@pipeline_options
@click.pass_obj
def swarm(app_manager, pipeline_name, runtime):
    """Deploy services in a docker swarm."""
    # need to implement docker service api run
    raise NotImplementedError

    # start = round(time.time())
    #
    # def stream_container_logs(cont: 'docker.models.containers.Container'):
    #     # get rid of uuid
    #     name = '.'.join(cont.name.split('.')[:-1]) if '.' in cont.name else cont.name
    #
    #     for log in cont.logs(stream=True, since=start):
    #         app_manager.thread_logs[name] += [log.decode()]
    #
    # for container in docker.from_env().containers.list(all=True):
    #     app_manager.thread(target=stream_container_logs, args=[container])


@pipeline.command()
@pipeline_options
@click.pass_obj
def k8s(app_manager, pipeline_name, runtime):
    raise NotImplementedError

