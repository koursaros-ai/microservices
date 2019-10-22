
from koursaros.credentials import get_creds
from ..decorators import *
import docker


@click.group()
def build():
    """Build docker images."""


@build.command()
@pipeline_options
@click.option('-p', '--push', is_flag=True)
@click.option('-c', '--creds')
def pipeline(app_manager, pipeline_name, runtime, yes, push, creds):
    """Build images for a pipeline. """

    if push:
        if creds is None:
            raise ValueError('--creds repository must be specified if pushing')

        hub_creds = get_creds(creds).dockerhub
        hub_auth = dict(username=hub_creds.username, password=hub_creds.password)

    app_manager.subprocess_call('eval $(minikube docker-env)', shell=True)

    docker_client = docker.from_env()
    flow = app_manager.get_flow('pipelines', pipeline_name, runtime).build()
    flow.to_helm_yaml()

    def docker_build(path, tag):
        app_manager.logger.critical('Building %s from %s...' % (tag, path))
        image, response = docker_client.images.build(path=path, tag=tag)
        for res in response:
            app_manager.logger.info(res)

        if push:
            app_manager.logger.critical('Pushing %s...' % tag)
            response = docker_client.images.push(tag, auth_config=hub_auth)
            for res in response:
                app_manager.logger.info(res)

    for service in flow.helm_yaml.values():
        service_type = service['image'].split('-')[1].split(':')[0]
        path = str(app_manager.find_app_file('services', service_type + 's', service['name'], 'Dockerfile'))
        docker_build(path, service['image'])

    if hasattr(flow, '_client_node'):
        client_cls = flow.client_node['name']
        path = str(app_manager.find_app_file('clients', client_cls, 'Dockerfile'))
        tag = 'gnes-client:%s' % client_cls
        docker_build(path, tag)

