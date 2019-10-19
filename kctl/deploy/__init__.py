
import click


@click.group()
@click.argument('runtime')
@click.pass_context
def deploy(ctx, runtime):
    """Deploy gnes services."""
    ctx.obj = (ctx.obj, runtime)


@click.group()
@click.argument('pipeline_name')
@click.pass_context
def pipeline(ctx, pipeline_name):
    """Deploy a pipeline with compose or k8s. """
    ctx.obj += (pipeline_name,)


deploy.add_command(pipeline)


@deploy.command()
@click.argument('client_name')
@click.argument('yaml_path')
@click.option('-c', '--creds', required=True)
@click.pass_obj
def client(obj, client_name, yaml_path, creds):
    """Deploy a client with docker. """
    app_manager, runtime = obj
    run_path = app_manager.find_app_file('clients', client_name, yaml_path)
    tag = 'clients:%s-%s' % (client_name, run_path.stem)
    build = ['docker', 'build', '-f', str(run_path), '-t', tag, '.']
    run = ['docker', 'run', '--network', 'host', '-it', tag, '--mode', runtime, '--creds', creds]

    app_manager.subprocess_call(build)
    app_manager.subprocess_call(run)


@pipeline.command()
@click.pass_obj
def compose(obj):
    app_manager, runtime, pipeline_name = obj
    run_path = str(app_manager.find_app_file('pipelines', pipeline_name, runtime, 'docker-compose.yml'))

    prefix = ['docker-compose', '-f']
    down = prefix + [run_path, 'down']
    up = prefix + [run_path, 'up', '--build']

    app_manager.subprocess_call(down)
    app_manager.subprocess_call(up)


def k8s(*args, **kwargs):
    raise NotImplementedError

