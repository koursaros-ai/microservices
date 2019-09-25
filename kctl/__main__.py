

def allow_keyboard_interrupt(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print()
            raise SystemExit

    return wrapper


@allow_keyboard_interrupt
def deploy_app(args):

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
    #     from .create import build_trigger
    #     from .create import build_cloudbuild
    #     from .create import build_deployment
    #     from .create import build_dockerfile
    #     from .create import git_push
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
def deploy_pipeline(args):

    raise SystemExit


@allow_keyboard_interrupt
def create_app(args):

    raise SystemExit
    from .create import create_microservice
    from .constants import CREATE


    create_microservice()


@allow_keyboard_interrupt
def create_pipeline(args):

    raise SystemExit
    from .create import create_microservice
    from .constants import CREATE



@allow_keyboard_interrupt
def create_service(args):
    from .create.service import main
    main(args)

    print(args)
    raise SystemExit


    create_microservice()


@allow_keyboard_interrupt
def create_model(args):
    raise SystemExit
    from .create import create_microservice
    from .constants import CREATE


    create_microservice()


@allow_keyboard_interrupt
def pull_app(args):
    from git import Repo
    Repo.clone_from(args.git, args.name)
    if args.dir:
        from distutils.dir_util import copy_tree
        copy_tree(f'{args.name}/{args.dir}', args.name)


def main():
    from .logger import redirect_out
    redirect_out()

    import argparse
    from .constants import DESCRIPTION

    # kctl
    kctl_parser = argparse.ArgumentParser(description=DESCRIPTION, prog='kctl')
    kctl_subparsers = kctl_parser.add_subparsers()

    # kctl create
    kctl_create_parser = kctl_subparsers.add_parser(
        'create',
        description='create an app, pipeline, service, or model'
    )
    kctl_create_subparsers = kctl_create_parser.add_subparsers()
    # kctl create app
    kctl_create_app_parser = kctl_create_subparsers.add_parser('app')
    kctl_create_app_parser.set_defaults(func=create_app)
    kctl_create_app_parser.add_argument('name')
    # kctl create pipeline
    kctl_create_pipeline_parser = kctl_create_subparsers.add_parser('pipeline')
    kctl_create_pipeline_parser.set_defaults(func=create_pipeline)
    kctl_create_pipeline_parser.add_argument('name')
    # kctl create service
    kctl_create_service_parser = kctl_create_subparsers.add_parser('service')
    kctl_create_service_parser.set_defaults(func=create_service)
    kctl_create_service_parser.add_argument('name')
    # kctl create model
    kctl_create_model_parser = kctl_create_subparsers.add_parser('model')
    kctl_create_model_parser.set_defaults(func=create_model)
    kctl_create_model_parser.add_argument('name')
    kctl_create_model_parser.add_argument('--base_image', default='koursaros-base')

    # kctl deploy
    kctl_deploy_parser = kctl_subparsers.add_parser(
        'deploy',
        description='deploy an app or pipeline'
    )
    kctl_deploy_subparsers = kctl_deploy_parser.add_subparsers()
    # kctl deploy app
    kctl_deploy_app_parser = kctl_deploy_subparsers.add_parser('app')
    kctl_deploy_app_parser.set_defaults(func=deploy_app)
    kctl_deploy_app_parser.add_argument('name')
    kctl_deploy_app_parser.add_argument(
        '-c', '--connection',
        action='store',
        help='connection parameters to use from koursaros.yaml'
    )
    # kctl deploy pipeline
    kctl_deploy_pipeline_parser = kctl_deploy_subparsers.add_parser('pipeline')
    kctl_deploy_pipeline_parser.set_defaults(func=deploy_pipeline)
    kctl_deploy_pipeline_parser.add_argument('name')
    kctl_deploy_pipeline_parser.add_argument(
        '-c', '--connection',
        action='store',
        help='connection parameters to use from koursaros.yaml'
    )

    # kctl pull
    kctl_pull_parser = kctl_subparsers.add_parser(
        'pull',
        description='pull an app'
    )
    kctl_pull_subparsers = kctl_pull_parser.add_subparsers()
    # kctl pull app
    kctl_pull_app_parser = kctl_pull_subparsers.add_parser('app')
    kctl_pull_app_parser.set_defaults(func=pull_app)
    kctl_pull_app_parser.add_argument('name')
    kctl_pull_app_parser.add_argument(
        '-g', '--git',
        action='store',
        help='pull an app from a git directory'
    )
    kctl_pull_app_parser.add_argument(
        '-d', '--dir',
        action='store',
        help='which directory the app is in'
    )

    args = kctl_parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
