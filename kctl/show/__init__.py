import click
from importlib import machinery
import webbrowser
import os


@click.group()
@click.argument('runtime')
@click.pass_context
def show(ctx, runtime):
    """Deploy gnes services."""
    ctx.obj = (ctx.obj, runtime)


@show.command()
@click.argument('pipeline_name')
@click.option('-s', '--save', is_flag=True)
@click.pass_obj
def pipeline(obj, pipeline_name, save):
    """Deploy a pipeline with compose or k8s. """
    app_manager, runtime = obj
    flow_path = app_manager.find_app_file('pipelines', pipeline_name, runtime, 'flow.py')
    os.chdir(str(flow_path.parent))
    flow = machinery.SourceFileLoader('flow', str(flow_path)).load_module().flow
    build = flow.build()
    url = build.to_url()
    try:
        webbrowser.open_new_tab(url)
    except webbrowser.Error as ex:
        app_manager.logger.critical(
            '%s\nCould not open browser... Please visit:\n%s' % (ex, url))

    if save:
        out_path = flow_path.parent.joinpath('docker-compose-temp.yml')
        out_path.write_text(build.to_swarm_yaml())
        app_manager.logger.critical('Saved swarm yaml to %s' % str(out_path))


def k8s(*args, **kwargs):
    raise NotImplementedError
