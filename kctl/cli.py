""".

kctl controls the \033[1;4mKoursaros\033[0m platform.
Find more information at: https://github.com/koursaros-ai/koursaros

."""


from .utils import PathManager
from .logger import KctlLogger
from .create import create
from .deploy import deploy
from .train import train
from .pull import pull
from .save import save
import click


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = PathManager()
    KctlLogger.init()


cli.add_command(create)
cli.add_command(deploy)
cli.add_command(train)
cli.add_command(pull)
cli.add_command(save)

cli(prog_name=__package__)
