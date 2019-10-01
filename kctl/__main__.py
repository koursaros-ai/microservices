
from kctl.cli import get_args


def main():
    args = get_args()
    print(args)
    raise KeyError('aaaaaay')
    args.func(args)
