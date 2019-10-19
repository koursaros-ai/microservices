
import click
from importlib import machinery


@click.group()
@click.argument('runtime')
@click.pass_context
def show(ctx, runtime):
    """Deploy gnes services."""
    ctx.obj = (ctx.obj, runtime)


@show.command()
@click.argument('pipeline_name')
@click.pass_obj
def pipeline(obj, pipeline_name):
    """Deploy a pipeline with compose or k8s. """
    app_manager, runtime = obj
    flow_path = app_manager.find_app_file('pipelines', pipeline_name, runtime, 'flow.py')
    flow = machinery.SourceFileLoader('flow', flow_path).load_module()
    import pdb
    pdb.set_trace()


def k8s(*args, **kwargs):
    raise NotImplementedError

