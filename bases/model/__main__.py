from shared.modeling import get_model
import sys

@stub
def subber(*args):
    return model.run(args)

if __name__ == '__main__':
    name = sys.argv[0]
    model = get_model(name)