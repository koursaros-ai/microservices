
import yaml


class Yamls:
    def update(self, **entries):
        self.__dict__.update(entries)

    def append(self, ):


def yaml_safe_load(root, file):
    with open(root + '/' + file) as fh:
        return yaml.safe_load(fh)


def compile_yamls(app_path):
    import os

    yamls = Yamls()

    yam = yaml_safe_load(app_path, 'connections.yaml')
    yamls.update(**yam)

    # pipelines = app_path + '/pipelines'
    # for pipeline in os.listdir(pipelines):
    #     yam = yaml_safe_load(pipelines, file)
    #     print(yam)
    #     yamls.add(**yam)
    #
    #
    #         elif file == 'service.yaml':
    #             yam = yaml_safe_load(root, file)
    #             yamls.add(**yam)
    #
    #         elif file == 'stubs.yaml':


    print(dir(yamls.connections))
