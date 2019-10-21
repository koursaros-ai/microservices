from ..decorators import *
import koursaros
from shutil import copytree
from pathlib import Path


@click.group()
def save():
    """Save gnes deployment as swarm, minikube, k8s, or shell."""


@save.command()
@pipeline_options
@click.argument('platform')
@click.pass_obj
def pipeline(app_manager, pipeline_name, runtime, platform):
    """Deploy a pipeline with compose or k8s. """
    flow = app_manager.get_flow('pipelines', pipeline_name, runtime).build()

    if platform == 'swarm':
        flow.path.parent.joinpath('docker-compose.yaml').write_text(flow.to_swarm_yaml())

    elif platform == 'helm':
        copytree(Path(koursaros.__path__).joinpath('charts', 'gnes'), str(flow.path.parent))
        flow.path.parent.joinpath('gnes', 'values.yaml').write_text(flow.to_helm_yaml())

    else:
        raise NotImplementedError

    app_manager.logger.critical('Saved %s yaml to %s' % (platform, str(flow.path.parent)))
