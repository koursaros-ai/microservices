
from .manager import AppManager
from .deploy import deploy
from .test import test
from .show import show
from .build import build
import click


@click.group()
@click.pass_context
def kctl(ctx):
    """
    kctl controls the \033[1;3;4;34mKoursaros\033[0m platform.
    Find more information at: https://github.com/koursaros-ai/koursaros
    """
    ctx.obj = AppManager()


kctl.add_command(deploy)
kctl.add_command(test)
kctl.add_command(show)
kctl.add_command(build)


def main():
    kctl(prog_name=__package__)


if __name__ == "__main__":
    main()
