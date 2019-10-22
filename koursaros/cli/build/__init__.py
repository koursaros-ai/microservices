from koursaros.repo_creds import get_creds
from ..decorators import *
import docker


@click.group()
def build():
    """Build docker images."""


@build.command()
@pipeline_options
@click.option('-p', '--push', is_flag=True)
@click.option('-c', '--creds')
def pipeline(app_manager, flow_name, runtime, yes, push, creds):
    """Build images for a pipeline. """

    if yes:
        if creds is None:
            raise ValueError('--creds repository must be specified if pushing')

        hub_creds = get_creds(creds).dockerhub
        app_manager.subprocess_call('docker login -u %s -p %s' % (
            hub_creds.username, hub_creds.password), shell=True)

    app_manager.subprocess_call('eval $(minikube docker-env)', shell=True)

    flow = app_manager.get_flow('flows', flow_name, runtime).build()
    flow.to_helm_yaml()

    def docker_build(path, tag):
        app_manager.logger.critical('Building %s from %s...' % (tag, path))
        app_manager.subprocess_call('docker build -t %s %s' % (tag, path), shell=True)

        if push:
            app_manager.logger.critical('Pushing %s...' % tag)
            app_manager.subprocess_call('docker push %s' % tag, shell=True)

    for services in flow.helm_yaml.values():
        for service in services:
            if service['model']:
                path = str(app_manager.find('hub', service['app'], service['model']))
                docker_build(path, service['image'])

    if hasattr(flow, '_client_node'):
        client_cls = flow.client_node['name']
        path = str(app_manager.find('clients', client_cls))
        tag = 'gnes-client:%s' % client_cls
        docker_build(path, tag)
