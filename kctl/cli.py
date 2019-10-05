""".

kctl controls the \033[1;4mKoursaros\033[0m platform.
Find more information at: https://github.com/koursaros-ai/koursaros

."""


from .utils import PathManager
from .create import create
from .deploy import deploy
from .train import train
from .pull import pull
import click


@click.group()
@click.pass_context
def kctl(ctx):
    ctx.obj = PathManager()


kctl.add_command(create)
kctl.add_command(deploy)
kctl.add_command(train)
kctl.add_command(pull)


def cli():
    kctl(prog_name=__package__)


if __name__ == "__main__":
    cli()
