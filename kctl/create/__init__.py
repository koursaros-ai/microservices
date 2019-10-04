import click


@click.group()
@click.pass_context
def create(ctx):
    """Create a pipeline or service"""
    pass


@create.command()
@click.pass_obj
def pipeline(args):
    must_not_be_pipe_path()
    new_pipe_path = f'{CWD}/{args.pipeline_name}'
    copytree(PIPE_TEMPLATE_PATH, new_pipe_path)
    os.makedirs(f'{new_pipe_path}/{HIDDEN_DIR}', exist_ok=True)
    open(f'{new_pipe_path}/{HIDDEN_DIR}/__init__.py', 'w')
    print(f'Created pipeline: {new_pipe_path}')


@create.command()
@click.pass_obj
def service(args):
    must_be_pipe_path()
    services_path = f'{PIPE_PATH}/services/'
    os.makedirs(services_path, exist_ok=True)
    new_service_path = services_path + args.service_name
    copytree(SERVICE_TEMPLATE_PATH, new_service_path)
    print(f'Created service: {new_service_path}')