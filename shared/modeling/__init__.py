from yaml import load, dump, FullLoader
from box import Box
from shared.modeling.models import MODELS
import hashlib

def model_filename_resolver(name):
    if name.split('.')[-1] == 'yaml':
        return name
    return f'./services/{name}.yaml'

def model_from_yaml(filename):
    with open(filename, 'r') as stream:
        config = Box(load(stream, Loader=FullLoader))
        md5 = hashlib.md5()
        md5.update(stream.read().encode())
        for model_class in MODELS:
            if config.base in model_class.architectures():
                model = model_class(config, md5.hexdigest())
                return model

def get_model(name):
    filename = model_filename_resolver(name)
    return model_from_yaml(filename)