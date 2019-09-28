import sys
from threading import Thread
from kctl.utils import find_app_path
from kctl.logger import redirect_out
import pickle
from kctl.cli import get_args


class Service:
    __slots__ = ['stubs']

    def __init__(self, file, prefetch=1):

        app_path = find_app_path(file)
        sys.path.append(f'{app_path}/.koursaros/')

        service = file.split('/')[-2]
        redirect_out(service)
        args = get_args()

        with open(app_path + '/.koursaros/app.pickle', 'rb') as fh:
            app = pickle.load(fh)

        self.stubs = app.configure(args.pipelines, service, args.connection, prefetch)

    def stub(self, name):
        def decorator(func):
            self.stubs[name].func = func
            return func
        return decorator

    def run(self):
        threads = []
        for name, stub in self.stubs.items():
            t = Thread(target=stub.consume)
            print(f'Starting thread {t.getName()}: "{name}"')
            t.start()
            threads.append(t)

        for t in threads:
            print(f'Waiting to finish {t.getName()}: "{name}"')
            t.join()
