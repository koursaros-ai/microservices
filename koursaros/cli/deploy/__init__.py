
from ..decorators import *
from tqdm import tqdm
import time


@click.group()
def deploy():
    """Deploy gnes services."""


@deploy.command()
@pipeline_options
@click.option('-p', '--platform', type=click.Choice(['compose', 'swarm', 'k8s']))
@click.option('-d', '--dryrun', is_flag=True)
def flow(app_manager, flow_name, runtime, platform, dryrun):
    """Deploy a pipeline with compose or k8s. """
    _flow = app_manager.get_flow(flow_name, runtime)
    swarm_path = _flow.path.parent.joinpath('docker-compose.yml')
    helm_path = _flow.path.parent.joinpath('helm')

    if platform == 'compose':
        down = 'docker-compose -f %s down' % str(swarm_path)
        app_manager.subprocess_call(down, shell=True)
        up = 'docker-compose -f %s up' % str(swarm_path)
        app_manager.subprocess_call(up, shell=True)

    elif platform == 'swarm':
        rm = 'docker stack rm %s' % flow_name
        app_manager.subprocess_call(rm, shell=True)
        app_manager.logger.critical('Waiting for docker network resources...')
        [time.sleep(0.15) for _ in tqdm(range(100))]
        stack = 'docker stack deploy --compose-file %s %s' % (str(swarm_path), flow_name)
        app_manager.subprocess_call(stack, shell=True)

    if platform == 'k8s':
        purge = 'helm delete --purge $(helm ls --all --short)'
        app_manager.subprocess_call(purge, shell=True)
        install = 'helm install ' + ('--dry-run --debug ' if dryrun else '') + str(helm_path)
        app_manager.subprocess_call(install, shell=True)


@deploy.command()
@client_options
def client(app_manager, flow_name, runtime, creds):
    """Deploy a client with docker. """
    _flow = app_manager.get_flow(flow_name, runtime)
    tag = 'hub-client:latest-%s' % _flow.client_node.pop('model')
    path = _flow.client_node.pop('yaml_path')
    app_manager.subprocess_call(
        'docker run -i %s --mode %s --yaml_path %s --network %s --creds %s' % (
            tag, runtime, path, creds), shell=True)


