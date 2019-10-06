""".

kctl controls the \033[1;4mKoursaros\033[0m platform.
Find more information at: https://github.com/koursaros-ai/koursaros


."""


from .utils import AppManager
from .create import create
from .deploy import deploy
from .pull import pull
from .train import train
import click


@click.group()
@click.pass_context
def kctl(ctx):
    ctx.obj = AppManager()
    import pdb; pdb.set_trace()



kctl.add_command(create)
kctl.add_command(deploy)
kctl.add_command(pull)
kctl.add_command(train)


def cli():
    kctl(prog_name=__package__)


if __name__ == "__main__":
    cli()
