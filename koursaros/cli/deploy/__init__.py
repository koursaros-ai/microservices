
from ..decorators import *


@click.group()
def deploy():
    """Deploy gnes services."""


@deploy.command()
@pipeline_options
@click.option('-p', '--platform', type=click.Choice(['swarm', 'k8s']))
@click.option('-d', '--dryrun', is_flag=True)
def flow(app_manager, flow_name, runtime, platform, dryrun):
    """Deploy a pipeline with compose or k8s. """
    _flow = app_manager.get_flow(flow_name, runtime)

    if platform == 'swarm':
        swarm_path = _flow.path.parent.joinpath('docker-compose.yml')
        rm = 'docker stack rm %s' % flow_name
        stack = 'docker stack deploy --compose-file %s %s' % (str(swarm_path), flow_name)
        app_manager.subprocess_call(rm, shell=True)
        app_manager.subprocess_call(stack, shell=True)

    if platform == 'k8s':
        helm_path = _flow.path.parent.joinpath('helm')
        purge = 'helm delete --purge $(helm ls --all --short)'
        app_manager.subprocess_call(purge, shell=True)
        install = 'helm install ' + ('--dry-run --debug ' if dryrun else '') + str(helm_path)
        app_manager.subprocess_call(install, shell=True)



@deploy.command()
@client_options
def client(app_manager, flow_name, runtime, creds):
    """Deploy a client with docker. """
    _flow = app_manager.get_flow(flow_name, runtime)
    tag = 'hub-client:latest-%s' % _flow.client_node.pop('name')
    app_manager.subprocess_call(
        'docker run -it %s --mode %s --creds %s' % (tag, runtime, creds), stream=True)


