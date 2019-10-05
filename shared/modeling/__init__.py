from yaml import load, dump, FullLoader
from box import Box
from shared.modeling.models import MODELS

def model_filename_resolver(name):
    if name.split('.')[-1] == 'yaml':
        return name
    return f'./services/{name}.yaml'

def model_from_yaml(filename):
    with open(filename, 'r') as stream:
        config = Box(load(stream, Loader=FullLoader))
        print(config.type)

def get_model(name):
    filename = model_filename_resolver(name)
    model_from_yaml(filename)