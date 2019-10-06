import sys
from koursaros.modeling import get_model

def train(file):
    model = get_model(file)
    model.train()


if __name__ == '__main__':
    filename = sys.argv[1]
    train(filename)