from yaml import load, dump

def model_from_yaml(filename):
    with open(filename, 'r') as stream:
        config = load(stream)
        print(config)