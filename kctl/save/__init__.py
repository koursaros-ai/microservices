from ..decorators import *
from .utils import *
from ruamel import yaml
import re


@click.group()
def save():
    """Save gnes deployment as swarm, minikube, k8s, or shell."""


@save.command()
@pipeline_options
@click.option('-f', '--filename', required=True)
@click.pass_obj
def pipeline(app_manager, pipeline_name, runtime, platform, filename):
    """Deploy a pipeline with compose or k8s. """
    flow = app_manager.get_flow('pipelines', pipeline_name, runtime).build()
    out_path = flow.path.parent.joinpath(filename)

    if platform == 'swarm':
        out_path.write_text(flow.to_swarm_yaml())

    elif platform == 'helm':
        values = yaml.load(flow.to_swarm_yaml())
        dict_merge(values['services'], flow._service_nodes)
        out_path.write_text(re.sub('!!python.*?\n', '\n', yaml.dump(values)))

    elif platform == 'shell':
        raise NotImplementedError

    app_manager.logger.critical('Saved %s yaml to %s' % (platform, str(out_path)))
