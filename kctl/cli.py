
from kctl.deploy.checks import check_rabbitmq
from kctl.deploy.rabbitmq import bind_rabbitmq
from koursaros.compile import compile_pipeline
from koursaros.utils import find_pipe_path
from shutil import rmtree, copytree
import koursaros.compile
from subprocess import call
import importlib
import argparse
import kctl
import os

SAVE_PATH = koursaros.__path__[0] + '/pipelines/'
koursaros.compile.set_imports(SAVE_PATH)

CWD = os.getcwd()
PIPE_PATH = find_pipe_path(CWD)
PIPE_NAME = PIPE_PATH.split('/')[-2] if PIPE_PATH else None
KCTL_PATH = kctl.__path__[0]
PIPE_TEMPLATE_PATH = KCTL_PATH + '/create/template/pipeline'
SERVICE_TEMPLATE_PATH = KCTL_PATH + '/create/template/pipeline/services/service'
HIDDEN_DIR = '.koursaros'
CACHE_DIR = '.kctlcache'


KCTL_DESC = '''
kctl controls the \033[1;4mKoursaros\033[0m platform.
Find more information at: https://github.com/koursaros-ai/koursaros

'''

CREATE_ARGS = ('create',)
DEPLOY_ARGS = ('deploy',)
SAVE_ARGS = ('save',)
TRAIN_ARGS = ('train',)
SAVE_PIPE_ARGS = ('pipeline',)
CREATE_PIPE_ARGS = ('pipeline',)
CREATE_SERVICE_ARGS = ('service',)
PULL_ARGS = ('pull',)
GIT_ARGS = ('-g', '--git')
DIR_ARGS = ('-d', '--dir')

KCTL_KWARGS = {'description': KCTL_DESC, 'prog': 'kctl'}
CREATE_KWARGS = {'description': 'create an pipeline, backend, or model'}
DEPLOY_KWARGS = {'description': 'Check configuration yamls, bind rabbitmq, and deploy'}
SAVE_KWARGS = {'description': f'compile and save to {SAVE_PATH}'}
PULL_KWARGS = {'description': 'pull an app'}
TRAIN_KWARGS = {'description': 'train a model'}
GIT_KWARGS = {'help': 'pull a pipeline from a git directory'}
CONNECTION_ARGS = ('-c', '--connection')
CONNECTION_KWARGS = {
    'action': 'store',
    'required': True,
    'help': 'connection parameters to use from connections.yaml',
}
REBIND_ARGS = ('-r', '--rebind')
REBIND_KWARGS = {
    'action': 'store_true',
    'help': 'clear and rebind the rabbitmq binds on entrance'
}
DIR_KWARGS = {'action': 'store', 'help': 'which directory the pipeline is in'}


class KctlError(Exception):
    pass


def must_be_pipe_path():
    if PIPE_PATH is None:
        raise KctlError(f'"{CWD}" is not a pipeline')


def must_not_be_pipe_path():
    if PIPE_PATH is not None:
        raise KctlError(f'"{PIPE_PATH}" is already a pipeline')


def save_pipeline(args):
    must_be_pipe_path()
    compile_pipeline(PIPE_PATH, SAVE_PATH)


def deploy_pipeline(args):
    must_be_pipe_path()
    save_pipeline(args)
    from koursaros import pipelines
    importlib.reload(pipelines)
    check_rabbitmq(args)
    if args.rebind:
        bind_rabbitmq(args)
    from .deploy import deploy_pipeline
    deploy_pipeline(PIPE_PATH, args)


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


def create_pipeline(args):
    must_not_be_pipe_path()
    new_pipe_path = f'{CWD}/{args.pipeline_name}'
    copytree(PIPE_TEMPLATE_PATH, new_pipe_path)
    os.makedirs(f'{new_pipe_path}/{HIDDEN_DIR}', exist_ok=True)
    open(f'{new_pipe_path}/{HIDDEN_DIR}/__init__.py', 'w')
    print(f'Created pipeline: {new_pipe_path}')


def create_service(args):
    must_be_pipe_path()
    services_path = f'{PIPE_PATH}/services/'
    os.makedirs(services_path, exist_ok=True)
    new_service_path = services_path + args.service_name
    copytree(SERVICE_TEMPLATE_PATH, new_service_path)
    print(f'Created service: {new_service_path}')


def train_model(args):
    raise NotImplementedError


def pull_pipeline(args):
    must_not_be_pipe_path()
    call(['git', 'clone', args.git, args.name])

    if args.dir:
        copytree(f'{args.name}/{args.dir}', CACHE_DIR)
        rmtree(args.name)
        copytree(CACHE_DIR, args.name)
        rmtree(CACHE_DIR)


def get_args():

    parser = argparse.ArgumentParser(**KCTL_KWARGS)
    parser.set_defaults(pipeline_name=PIPE_NAME)
    subparsers = parser.add_subparsers()

    # SAVE
    save_parser = subparsers.add_parser(*SAVE_ARGS, **SAVE_KWARGS)
    save_subparsers = save_parser.add_subparsers()
    # save pipeline
    save_pipeline_parser = save_subparsers.add_parser(*SAVE_PIPE_ARGS)
    save_pipeline_parser.set_defaults(func=save_pipeline)

    # CREATE
    create_parser = subparsers.add_parser(*CREATE_ARGS, **CREATE_KWARGS)
    create_subparsers = create_parser.add_subparsers()
    # create pipeline
    create_pipeline_parser = create_subparsers.add_parser(*CREATE_PIPE_ARGS)
    create_pipeline_parser.set_defaults(func=create_pipeline)
    create_pipeline_parser.add_argument('pipeline_name')
    # create service
    create_service_parser = create_subparsers.add_parser(*CREATE_SERVICE_ARGS)
    create_service_parser.set_defaults(func=create_service)
    create_service_parser.add_argument('service_name')

    # TRAIN
    train_parser = subparsers.add_parser(*TRAIN_ARGS, **TRAIN_KWARGS)
    train_subparsers = train_parser.add_subparsers()
    # train model
    train_model_parser = train_subparsers.add_parser('model')
    train_model_parser.set_defaults(func=train_model)
    train_model_parser.add_argument('model_name')
    train_model_parser.add_argument('--base_image', default='koursaros-base')

    # DEPLOY
    deploy_parser = subparsers.add_parser(*DEPLOY_ARGS, **DEPLOY_KWARGS)
    deploy_subparsers = deploy_parser.add_subparsers()
    # deploy pipeline
    deploy_pipeline_parser = deploy_subparsers.add_parser('pipeline')
    deploy_pipeline_parser.set_defaults(func=deploy_pipeline)
    deploy_pipeline_parser.add_argument(*CONNECTION_ARGS, **CONNECTION_KWARGS)
    deploy_pipeline_parser.add_argument(*REBIND_ARGS, **REBIND_KWARGS)
    deploy_pipeline_parser.add_argument('-d', '--debug', action='store_true')

    # kctl pull
    pull_parser = subparsers.add_parser(*PULL_ARGS, **PULL_KWARGS)
    pull_subparsers = pull_parser.add_subparsers()
    # kctl pull pipeline
    pull_pipeline_parser = pull_subparsers.add_parser('pipeline')
    pull_pipeline_parser.set_defaults(func=pull_pipeline)
    pull_pipeline_parser.add_argument('pipeline_name')

    pull_pipeline_parser.add_argument(*GIT_ARGS, **GIT_KWARGS)
    pull_pipeline_parser.add_argument(*DIR_ARGS, **DIR_KWARGS)

    return parser.parse_args()
