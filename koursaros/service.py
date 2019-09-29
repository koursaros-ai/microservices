import sys
from threading import Thread
from kctl.utils import find_app_path
from kctl.logger import redirect_out
import pickle
from kctl.cli import get_args


def Service(path, prefetch=1):

    pipe_path = find_app_path(path)
    sys.path.append(f'{pipe_path}/.koursaros/')
    name = path.split('/')[-2]
    args = get_args()

    with open(pipe_path + '/.koursaros/pipeline.pickle', 'rb') as fh:
        Pipeline = pickle.load(fh)

    service = Pipeline.services[name]
    for stub in service.stubs:
        stub.configure(args.connection, prefetch)

    return service


        self.stubs = app.configure(args.pipelines, service, args.connection, prefetch)
        self.messages = Messages(self.stubs)

    def run(self):
        threads = []
        for stub in self.stubs:
            t = Thread(target=stub.consume)
            print(f'Starting thread {t.getName()}: "{stub.name}"')
            t.start()
            threads.append((t, stub.name))

        for t, name in threads:
            print(f'Waiting to finish {t.getName()}: "{name}"')
            t.join()
