
import yaml


class Yamls:
    def add(self, **entries):
        self.__dict__.update(entries)


def compile_yamls(app_path):
    import os

    yamls = Yamls()

    for root, dirs, files in os.walk(app_path, topdown=False):
        for file in files:
            if file == 'connections.yaml':
                yam = yaml.safe_load(root + '/' + file)
                yamls.add(**yam)

            elif file == 'service.yaml':
                yam = yaml.safe_load(root + '/' + file)
                yamls.add(**yam)

            elif file == 'stubs.yaml':
                yam = yaml.safe_load(root + '/' + file)
                print(yam)
                yamls.add(**yam)

    print(dir(yamls))
