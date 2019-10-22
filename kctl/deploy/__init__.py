
from ..decorators import *
import docker


@click.group()
def deploy():
    """Deploy gnes services."""


@deploy.command()
@pipeline_options
@click.option('-p', '--platform', required=True)
@click.option('-d', '--dryrun', is_flag=True)
def pipeline(app_manager, pipeline_name, runtime, yes, platform, dryrun):
    """Deploy a pipeline with compose or k8s. """

    if platform == 'swarm':
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

    elif platform == 'k8s':
        helm_path = app_manager.find('pipelines', pipeline_name, runtime, 'helm')
        app_manager.subprocess_call('helm delete --purge $(helm ls --all --short)'.split())
        install = ['helm', 'install']
        if dryrun: install += ['--dry-run', '--debug']
        install += [str(helm_path)]
        app_manager.subprocess_call(install)


@deploy.command()
@client_options
def client(app_manager, pipeline_name, runtime, creds):
    """Deploy a client with docker. """
    flow = app_manager.get_flow('pipelines', pipeline_name, runtime)
    cn = flow.client_node
    tag = 'gnes-client:%s' % (cn.pop('name'))

    switches = ['--mode', runtime,
                '--creds', creds,
                ] + ['--%s %s' % (k, v) for k, v in cn.items()]

    response = docker.from_env().containers.run(tag, stream=True, command=switches)

    for stream in response:
        app_manager.logger.info(stream)


