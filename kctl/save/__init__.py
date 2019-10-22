from ..decorators import *
import koursaros
from shutil import copytree, rmtree
from pathlib import Path


@click.group()
def save():
    """Save gnes deployment as swarm, minikube, k8s, or shell."""


@save.command()
@pipeline_options
def pipeline(app_manager, pipeline_name, runtime, platform, yes):
    """Deploy a pipeline with compose or k8s. """
    flow = app_manager.get_flow('pipelines', pipeline_name, runtime).build()

    if platform == 'swarm':
        flow.path.parent.joinpath('docker-compose.yaml').write_text(flow.to_swarm_yaml())
        app_manager.logger.critical('Saved swarm yaml to %s' % str(flow.path.parent))

    elif platform == 'k8s':
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
            copytree(str(Path(koursaros.__path__[0]).joinpath('charts', 'gnes')), str(out_path))
            flow.path.parent.joinpath('helm', 'values.yaml').write_text(flow.to_helm_yaml())
            app_manager.logger.critical('Saved helm chart to %s' % str(out_path))

    else:
        raise NotImplementedError


