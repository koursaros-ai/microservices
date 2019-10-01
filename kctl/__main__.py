
from kctl.cli import get_args


def main():
    args = get_args('kctl')
    args.func(args)
