
import click
from tqdm import tqdm
import time


@click.group()
def deploy():
    """Deploy gnes services."""


@deploy.group()
def flow():
    """Deploy a pipeline with compose or k8s. """


deploy.add_command(flow)


@flow.command()
@click.argument('flow_name')
@click.pass_obj
def compose(app_manager, flow_name):
    path = app_manager.get_flow(flow_name).path.parent.joinpath('docker-compose.yml')
    down = 'docker-compose -f %s down' % str(path)
    app_manager.call(down, shell=True)
    up = 'docker-compose -f %s up' % str(path)
    app_manager.call(up, shell=True)


@flow.command()
@click.argument('flow_name')
@click.pass_obj
def swarm(app_manager, flow_name):
    path = app_manager.get_flow(flow_name).path.parent.joinpath('docker-compose.yml')
    rm = 'docker stack rm %s' % flow_name
    app_manager.call(rm, shell=True)
    app_manager.logger.critical('Waiting for docker network resources...')
    [time.sleep(0.15) for _ in tqdm(range(100))]
    stack = 'docker stack deploy --compose-file %s %s' % (str(path), flow_name)
    app_manager.call(stack, shell=True)


@flow.command()
@click.argument('flow_name')
@click.option('-d', '--dryrun', is_flag=True)
@click.pass_obj
def k8s(app_manager, flow_name, dryrun):
    path = app_manager.get_flow(flow_name).path.parent.joinpath('helm')
    purge = 'helm delete --purge $(helm ls --all --short)'
    app_manager.call(purge, shell=True)
    install = 'helm install ' + ('--dry-run --debug ' if dryrun else '') + str(path)
    app_manager.call(install, shell=True)


# @deploy.command()
# @click.option('-c', '--creds')
# def client(app_manager, flow_name, runtime, creds):
#     """Deploy a client with docker. """
#     _flow = app_manager.get_flow(flow_name, runtime)
#     tag = 'hub-client:latest-%s' % _flow.client_node.pop('model')
#     path = _flow.client_node.pop('yaml_path')
#     app_manager.subprocess_call(
#         'docker run --network %s -i %s --mode %s --yaml_path %s --creds %s' % (
#             'host', tag, runtime, path, creds), shell=True)
#

