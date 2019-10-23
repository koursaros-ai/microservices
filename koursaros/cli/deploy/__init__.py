
from ..decorators import *


@click.group()
def deploy():
    """Deploy gnes services."""


@deploy.command()
@pipeline_options
@click.option('-d', '--dryrun', is_flag=True)
def pipeline(app_manager, flow_name, runtime, yes, platform, dryrun):
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
        helm_path = app_manager.find('pipelines', flow_name, runtime, 'helm', pkg=True)
        purge = 'helm delete --purge $(helm ls --all --short)'
        app_manager.subprocess_call(purge, shell=True)
        install = 'helm install ' + '--dry-run --debug' if dryrun else '' + str(helm_path)
        app_manager.subprocess_call(install, shell=True)


@deploy.command()
@client_options
def client(app_manager, flow_name, runtime, creds):
    """Deploy a client with docker. """
    flow = app_manager.get_flow(flow_name, runtime)
    tag = 'hub-client:latest-%s' % flow.client_node.pop('name')
    app_manager.subprocess_call(
        'docker run -it %s --mode %s --creds %s' % (tag, runtime, creds), stream=True)


