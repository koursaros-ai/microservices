import argparse

ALL_ARGS = ('--all', '-a')
ALL_KWARGS = {'action': 'store_true', 'help': 'get all microservices'}
MICROSERVICES_ARGS = ('microservices',)
MICROSERVICES_KWARGS = {'nargs': '*'}


def allow_keyboard_interrupt(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print()
            raise SystemExit

    return wrapper


@allow_keyboard_interrupt
def deploy():
    from .constants import PUSH
    pushparser = argparse.ArgumentParser(description=PUSH, prog='kctl push')
    pushparser.add_argument('push')
    pushparser.add_argument(
        '--connection', '-c',
        action='store',
        help='connection parameters to use from koursaros.yaml'
    )
    pushparser.add_argument(
        '--actions', '-x',
        action='store',
        help='action in actions.yaml to run',
        required=True,
        nargs='+'
    )
    pushparser.add_argument(
        '--bind', '-b',
        action='store_true',
        help='rebind and flush rabbitmq on entry according to actions.yaml'
    )
    pushparser.add_argument(*ALL_ARGS, **ALL_KWARGS)
    pushparser.add_argument(*MICROSERVICES_ARGS, **MICROSERVICES_KWARGS)

    pushargs = pushparser.parse_args()

    if not pushargs.all and not pushargs.microservices:
        log.exception('Must select microservices in kctl push')
        raise SystemExit

    # 1. Compile koursaros.proto located in koursaros/protos
    from koursaros.protos import codegen
    codegen()

    # 2. Check actions.yaml
    from .checks import check_stubs, check_protos, check_rabbitmq
    check_stubs()
    check_protos()

    from koursaros.utils.yamls import get_connection
    connection_name = pushargs.connection
    connection = get_connection(connection_name)
    check_rabbitmq(*connection)

    if pushargs.bind:
        from .rabbitmq import bind_rabbitmq
        bind_rabbitmq(pushargs.actions, *connection)

    if pushargs.all:
        raise NotImplementedError
    else:
        microservices = pushargs.microservices

    from koursaros.microservices import run_microservices
    run_microservices(microservices, pushargs.actions, connection_name, *connection)

    # else:
    #     from .builders import build_trigger
    #     from .builders import build_cloudbuild
    #     from .builders import build_deployment
    #     from .builders import build_dockerfile
    #     from .builders import git_push
    #
    #     import uuid
    #     tag = str(uuid.uuid4())[:8]
    #
    #     if pushargs.all:
    #         build_trigger(all=True)
    #         build_cloudbuild(tag, all=True)
    #         build_dockerfile(all=True)
    #         build_deployment(tag, all=True)
    #         git_push(all=True)
    #
    #     else:
    #         microservices = pushargs.microservices
    #         build_trigger(microservices=microservices)
    #         build_cloudbuild(tag, microservices=microservices)
    #         build_dockerfile(microservices=microservices)
    #         build_deployment(tag, microservices=microservices)
    #         git_push(microservices=microservices)


@allow_keyboard_interrupt
def create():
    from .builders import create_microservice
    from .constants import CREATE

    createargs = createparser.parse_args()

    create_microservice(createargs)


def handle_exceptions(type_, value, tb):
    logging.exception((type_, value, tb))


if __name__ == "__main__":

    import logging
    import sys
    from .logger import redirect_kctl_out

    redirect_kctl_out()

    print('erwe')

    print('hello')
    z = 1/0
    print('hll')
    raise SystemExit
    # log = logging.getLogger('kctl')
    # sys.stdout = LoggerWriter()
    # sys.stderr = LoggerWriter()
    # handler = handle(sys.stdout)
    # handler.setLevel(logging.INFO)
    #
    # logger.addHandler(handler)

    from .constants import DESCRIPTION

    kctl_parser = argparse.ArgumentParser(description=DESCRIPTION, prog='kctl')
    kctl_subparsers = kctl_parser.add_subparsers()

    kctl_create_parser = kctl_subparsers.add_parser('create')
    kctl_create_subparsers = kctl_create_parser.add_subparsers()
    kctl_create_app_parser = kctl_create_subparsers.add_parser('app')
    kctl_create_app_parser.add_argument('name')
    kctl_create_pipeline_parser = kctl_create_subparsers.add_parser('pipeline')
    kctl_create_pipeline_parser.add_argument('name')
    kctl_create_service_parser = kctl_create_subparsers.add_parser('service')
    kctl_create_service_parser.add_argument('name')
    kctl_create_model_parser = kctl_create_subparsers.add_parser('model')
    kctl_create_model_parser.add_argument('name')
    kctl_create_model_parser.add_argument('--base_image', default='koursaros-base')

    kctl_deploy_parser = kctl_subparsers.add_parser('deploy')
    kctl_deploy_subparsers = kctl_deploy_parser.add_subparsers()
    kctl_deploy_app_parser = kctl_deploy_subparsers.add_parser('app')
    kctl_deploy_app_parser.add_argument('name')
    kctl_deploy_pipeline_parser = kctl_deploy_subparsers.add_parser('pipeline')
    kctl_deploy_pipeline_parser.add_argument('name')

    args = kctl_parser.parse_args()

    print(args)
    # argfunc = choices[cmdargs.command]
    # argfunc()
