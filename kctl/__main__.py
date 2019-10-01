
from kctl.cli import get_args


def main():
    args = get_args('kctl')
    print(args)
    raise KeyError('aaaaaay')
    args.func(args)
