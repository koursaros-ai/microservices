from yaml import load, dump

def model_filename_resolver(name):
    return f'./services/{name}.yaml'

def model_from_yaml(filename):
    with open(filename, 'r') as stream:
        config = load(stream)
        print(config)

def get_model(name):
    filename = model_filename_resolver(name)
    model_from_yaml(filename)