
from .manager import AppManager
from .create import create
from .deploy import deploy
from .train import train
from .pull import pull
from .config import credentials
import click


@click.group()
@click.pass_context
def kctl(ctx):
    """.

    kctl controls the \033[1;4mKoursaros\033[0m platform.
    Find more information at: https://github.com/koursaros-ai/koursaros


    ."""
    ctx.obj = AppManager()


kctl.add_command(create)
kctl.add_command(deploy)
kctl.add_command(pull)
kctl.add_command(train)
kctl.add_command(credentials)


def cli():
    kctl(prog_name=__package__)


if __name__ == "__main__":
    cli()
