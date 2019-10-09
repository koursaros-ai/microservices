import sys
from . import train

if __name__ == '__main__':
    filename = sys.argv[1]
    train(filename)