
from .cli import get_args


def main():
    args = get_args()
    args.func(args)
