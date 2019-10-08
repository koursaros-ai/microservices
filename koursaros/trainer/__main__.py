import sys
from koursaros.modeling import model_from_yaml

def train(file):
    model = model_from_yaml(file, training=True)
    model.train()

if __name__ == '__main__':
    filename = sys.argv[1]
    train(filename)