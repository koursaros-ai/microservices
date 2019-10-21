import click
from .helper import *
from ruamel import yaml
import re

@click.group()
def save():
    """Save gnes deployment as swarm, minikube, k8s, or shell."""


@save.command()
@click.argument('pipeline_name')
@click.option('-r', '--runtime', required=True)
@click.option('-p', '--platform', required=True, default='minikube',
              type=click.Choice(['k8s', 'swarm', 'shell']))
@click.pass_obj
def pipeline(app_manager, pipeline_name, runtime, platform):
    """Deploy a pipeline with compose or k8s. """
    flow = app_manager.get_flow('pipelines', pipeline_name, runtime)
    globals()[platform](flow.build(), app_manager.logger.critical)


def swarm(flow, log):
    out_path = flow.path.parent.joinpath('docker-compose-gen.yml')
    out_path.write_text(flow.to_swarm_yaml())
    log('Saved swarm yaml to %s' % str(out_path))


def k8s(flow, log):
    values = yaml.load(flow.to_swarm_yaml())
    dict_merge(values['services'], flow._service_nodes)
    out_path = flow.path.parent.joinpath('values-gen.yaml')
    out_path.write_text(re.sub(r'!!python*?\n', '', yaml.dump(values)))
    log('Saved values.yaml to %s' % str(out_path))
    import pdb
    pdb.set_trace()
