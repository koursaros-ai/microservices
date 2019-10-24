from koursaros.repo_creds import get_creds
import click
from shutil import copytree, rmtree


@click.group()
def build():
    """Build docker images."""


@build.command()
@click.argument('flow_name')
@click.option('-p', '--push')
@click.option('-c', '--creds')
@click.option('-n', '--no-caches', multiple=True)
@click.pass_obj
def flow(app_manager, flow_name, push, creds, no_caches):
    """Build images for a pipeline. """

    if push:
        if creds is None:
            raise ValueError('--creds repository must be specified if pushing')

        hub_creds = get_creds(creds).dockerhub
        app_manager.call('docker login -u %s -p %s' % (
            hub_creds.username, hub_creds.password), shell=True)

    # app_manager.call('eval $(minikube docker-env)', shell=True)

    _flow = app_manager.get_flow(flow_name).build()
    helm_yaml = _flow.to_helm_yaml()

    services = [apps for app in _flow.helm_yaml['services'].values() for apps in app]

    for service in services:
        if '/' in service['image']:
            app_manager.call('docker pull %s' % service['image'], shell=True)
        else:
            path = str(app_manager.find_model(service['app'], service['model']))
            tag = service['image']
            app_manager.logger.critical('Building %s from %s...' % (tag, path))
            cache = '--no-cache ' if service.get('name', None) in no_caches else ''
            _build = 'docker build ' + cache + '-t %s %s' % (tag, path)
            app_manager.call(_build, shell=True)

            if push:
                app_manager.logger.critical('Pushing %s...' % tag)
                app_manager.call('docker push %s/%s' % (push, tag), shell=True)

    """save swarm yaml"""
    out_path = _flow.path.parent.joinpath('docker-compose-temp.yml')
    out_path.write_text(_flow.to_swarm_yaml())
    app_manager.logger.critical('Saved swarm yaml to %s' % str(out_path))

    """save helm chart"""
    out_path = _flow.path.parent.joinpath('helm')
    rmtree(str(out_path), ignore_errors=True)
    copytree(str(app_manager.pkg_root.joinpath('chart')), str(out_path))
    _flow.path.parent.joinpath('helm/values.yaml').write_text(helm_yaml)
    app_manager.logger.critical('Saved helm chart to %s' % str(out_path))