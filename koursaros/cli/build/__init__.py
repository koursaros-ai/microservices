from koursaros.repo_creds import get_creds
from ..decorators import *
from shutil import copytree, rmtree
from pathlib import Path


@click.group()
def build():
    """Build docker images."""


@build.command()
@pipeline_options
@click.option('-p', '--push')
@click.option('-c', '--creds')
def pipeline(app_manager, flow_name, runtime, yes, push, creds):
    """Build images for a pipeline. """

    def docker_build(path, tag):
        app_manager.logger.critical('Building %s from %s...' % (tag, path))
        app_manager.subprocess_call('docker build -t %s %s' % (tag, path), shell=True)

        if push:
            app_manager.logger.critical('Pushing %s...' % tag)
            app_manager.subprocess_call('docker push %s/%s' % (push, tag), shell=True)

    if push:
        if creds is None:
            raise ValueError('--creds repository must be specified if pushing')

        hub_creds = get_creds(creds).dockerhub
        app_manager.subprocess_call('docker login -u %s -p %s' % (
            hub_creds.username, hub_creds.password), shell=True)

    app_manager.subprocess_call('eval $(minikube docker-env)', shell=True)

    flow = app_manager.get_flow('flows', flow_name, runtime).build()
    helm_yaml = flow.to_helm_yaml()

    for services in flow.helm_yaml.values():
        for service in services:
            if service['model']:
                path = str(app_manager.find('hub', service['app'], service['model']))
                docker_build(path, service['image'])

    if hasattr(flow, 'client_node'):
        model = Path(flow.client_node['yaml_path']).parent.name
        path = str(app_manager.find('hub', 'client', model))
        tag = 'gnes-client:latest-%s' % model
        docker_build(path, tag)

    """save helm chart"""
    out_path = flow.path.parent.joinpath('helm')
    if out_path.is_dir():
        if yes:
            rmtree(str(out_path))
        else:
            while True:
                yn = input('Overwrite %s? [y/n]' % str(out_path))
                if yn == 'y':
                    rmtree(str(out_path))
                    break
                elif yn == 'n':
                    break

    if not out_path.is_dir():
        copytree(str(app_manager.find('chart')), str(out_path))
        flow.path.parent.joinpath('helm', 'values.yaml').write_text(helm_yaml)
        app_manager.logger.critical('Saved helm chart to %s' % str(out_path))