import sys
from threading import Thread
from kctl.utils import find_app_path
from kctl.logger import redirect_out
import pickle
from kctl.cli import get_args

from koursaros.pipelines import Pigservice

pigservice = Pigservice(__file__)

@pigservice.pig.piggify
def hello(email):
    note = piggify.client.receive.Note()
    pggify.client.receive(note)



def Service(path, prefetch=1):


    class Args:
        def register_args(self, args):
            for arg, value in args.items():
                setattr(self, arg, value)


    pipe_path = find_app_path(path)
    sys.path.append(f'{pipe_path}/.koursaros/')
    name = path.split('/')[-2]
    args = get_args()

    with open(pipe_path + '/.koursaros/pipeline.pickle', 'rb') as fh:
        Pipeline = pickle.load(fh)

    service = Pipeline.services[name]
    service.configure(args.connection, prefetch)

    return service


