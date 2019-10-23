
from ..decorators import *


@click.group()
def deploy():
    """Deploy gnes services."""


@deploy.command()
@pipeline_options
@click.option('-d', '--dryrun', is_flag=True)
def flow(app_manager, flow_name, runtime, yes, dryrun):
    """Deploy a pipeline with compose or k8s. """
    helm_path = app_manager.get_flow(flow_name, runtime).path.parent.joinpath('helm')
    purge = 'helm delete --purge $(helm ls --all --short)'
    app_manager.subprocess_call(purge, shell=True)
    install = 'helm install ' + '--dry-run --debug' if dryrun else '' + str(helm_path)
    app_manager.subprocess_call(install, shell=True)


@deploy.command()
@client_options
def client(app_manager, flow_name, runtime, creds):
    """Deploy a client with docker. """
    _flow = app_manager.get_flow(flow_name, runtime)
    tag = 'hub-client:latest-%s' % _flow.client_node.pop('name')
    app_manager.subprocess_call(
        'docker run -it %s --mode %s --creds %s' % (tag, runtime, creds), stream=True)


