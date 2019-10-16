from koursaros.modeling.models import MODELS
from koursaros.yamls import Yaml
from kctl.logger import set_logger

logger = set_logger('MODELS')

def model_filename_resolver(name):
    if name.split('.')[-1] == 'yaml':
        return name
    return f'./services/{name}.yaml'

def model_from_yaml(filename, **kwargs):
    config = Yaml(filename)
    return model_from_config(config, **kwargs)

def model_from_config(config, training=False):
    for model_class in MODELS:
        if config.arch in model_class.architectures():
            model = model_class(config, training)
            logger.info('Loaded model {}'.format(config.arch))
            return model
    logger.error('Unsupported model architecture {}'.format(config.arch))
    raise NotImplementedError()
