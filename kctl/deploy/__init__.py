
import click
import subprocess


@click.group()
@click.pass_context
def deploy(ctx):
    """Deploy gnes services."""


@deploy.command()
@click.argument('pipeline_name')
@click.argument('runtime')
@click.argument('method', type=click.Choice(['k8s', 'compose']))
@click.pass_context
def pipeline(ctx, pipeline_name, runtime, method):
    """
    Deploy a pipeline with compose or k8s.
    """

    app_manager = ctx.obj
    app_manager.raise_if_not_app_root()
    run_path = app_manager.root.joinpath('pipelines', pipeline_name, runtime, 'docker-compose.yml')

    globals()[method](str(run_path), app_manager.logger.critical)


def compose(run_path, log):
    prefix = ['docker-compose', '-f']
    down = prefix + [run_path, 'down']
    up = prefix + [run_path, 'up --build']
    log('Calling %s' % ''.join(down))
    # subprocess.call(down)
    log('Calling %s' % ''.join(up))
    # subprocess.call(up)


def k8s(*args, **kwargs):
    raise NotImplementedError

