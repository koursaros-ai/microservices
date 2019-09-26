
import yaml


class Yamls:
    def add(self, **entries):
        self.__dict__.update(entries)


def yaml_safe_load(root, file):
    with open(root + '/' + file) as fh:
        return yaml.safe_load(fh)


def compile_yamls(app_path):
    import os

    yamls = Yamls()

    for root, dirs, files in os.walk(app_path, topdown=False):
        for file in files:
            if file == 'connections.yaml':
                yam = yaml_safe_load(root, file)
                yamls.add(**yam)

            elif file == 'service.yaml':
                yam = yaml_safe_load(root, file)
                yamls.add(**yam)

            elif file == 'stubs.yaml':
                yam = yaml_safe_load(root, file)
                print(yam)
                yamls.add(**yam)

    print(dir(yamls))
