import sys
from threading import Thread
from kctl.utils import find_app_path
from kctl.logger import redirect_out
import pickle
from kctl.cli import get_args


class Messages:
    def __init__(self, stubs):
        for stub in stubs:
            self.register_proto(stub.proto_in)
            self.register_proto(stub.proto_out)

    def register_proto(self, proto):
        if proto is not None:
            setattr(self, proto.__name__, proto)


class Service:
    __slots__ = ['stubs', 'messages', 'path', 'name']

    def __init__(self, path, prefetch=1):

        self.path = path
        pipe_path = find_app_path(path)
        sys.path.append(f'{pipe_path}/.koursaros/')
        self.name = path.split('/')[-2]
        args = get_args()

        with open(pipe_path + '/.koursaros/pipeline.pickle', 'rb') as fh:
            pipeline = pickle.load(fh)

        self.stubs = pipeline.services[self.name]
        self.stubs = app.configure(args.pipelines, service, args.connection, prefetch)
        self.messages = Messages(self.stubs)



    def stub(self, name):
        def decorator(func):
            self.stubs[name] = func
            return func
        return decorator

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
