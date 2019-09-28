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
    __slots__ = ['stubs', 'messages']

    def __init__(self, file, prefetch=1):

        app_path = find_app_path(file)
        sys.path.append(f'{app_path}/.koursaros/')
        service = file.split('/')[-2]
        args = get_args()

        with open(app_path + '/.koursaros/app.pickle', 'rb') as fh:
            app = pickle.load(fh)

        self.stubs = app.configure(args.pipelines, service, args.connection, prefetch)
        self.messages = Messages(self.stubs)

        # import pdb;
        # pdb.set_trace()

    def register_messagse(self):


    def stub(self, name):
        def decorator(func):
            for stub in self.stubs:
                if stub.name == name:
                    stub.func = func
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
