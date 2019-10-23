from koursaros.repo_creds import get_creds
from ..decorators import *
from shutil import copytree, rmtree


@click.group()
def build():
    """Build docker images."""


@build.command()
@pipeline_options
@click.option('-p', '--push')
@click.option('-c', '--creds')
@click.option('-n', '--no-cache', is_flag=True)
def flow(app_manager, flow_name, runtime, push, creds, no_cache):
    """Build images for a pipeline. """

    def docker_build(path, tag):
        app_manager.logger.critical('Building %s from %s...' % (tag, path))
        _build = 'docker build ' + ('--no-cache ' if no_cache else '') + '-t %s %s' % (tag, path)
        app_manager.subprocess_call(_build, shell=True)

        if push:
            app_manager.logger.critical('Pushing %s...' % tag)
            app_manager.subprocess_call('docker push %s/%s' % (push, tag), shell=True)

    if push:
        if creds is None:
            raise ValueError('--creds repository must be specified if pushing')

        hub_creds = get_creds(creds).dockerhub
        app_manager.subprocess_call('docker login -u %s -p %s' % (
            hub_creds.username, hub_creds.password), shell=True)

    # app_manager.subprocess_call('eval $(minikube docker-env)', shell=True)

    _flow = app_manager.get_flow(flow_name, runtime).build()
    helm_yaml = _flow.to_helm_yaml()
    _flow.helm_yaml['services']['client'] = [_flow.client_node]

    for app in _flow.helm_yaml.values():
        for services in app.values():
            for service in services:
                if '/' in service['image']:
                    app_manager.subprocess_call('docker pull %s' % service['image'], shell=True)
                else:
                    path = str(app_manager.find_model(service['app'], service['model']))
                    docker_build(path, service['image'])

    """save swarm yaml"""
    out_path = _flow.path.parent.joinpath('docker-compose.yml')
    out_path.write_text(_flow.to_swarm_yaml())

    """save helm chart"""
    out_path = _flow.path.parent.joinpath('helm')
    copytree(str(app_manager.find('chart', pkg=True)), str(out_path))
    _flow.path.parent.joinpath('helm/values.yaml').write_text(helm_yaml)
    app_manager.logger.critical('Saved helm chart to %s' % str(out_path))