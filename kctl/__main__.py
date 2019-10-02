
from kctl.cli import get_args
from kctl.logger import KctlLogger


def main():
    KctlLogger.init('kctl')
    args = get_args()
    args.func(args)
