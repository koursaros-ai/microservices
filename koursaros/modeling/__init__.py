from koursaros.modeling.models import MODELS
from koursaros.yamls import Yaml

def model_filename_resolver(name):
    if name.split('.')[-1] == 'yaml':
        return name
    return f'./services/{name}.yaml'

def model_from_yaml(filename):
    config = Yaml(filename)
    return model_from_config(config)

def model_from_config(config):
    for model_class in MODELS:
        if config.arch in model_class.architectures():
            model = model_class(config)
            return model
    print('unsupported model architecture {}'.format(config.arch))
    raise NotImplementedError()

def get_model(name):
    filename = model_filename_resolver(name)
    return model_from_yaml(filename)