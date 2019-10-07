import click
import sys
import os
from koursaros.yamls import Yaml

@click.command()
@click.argument('file')
@click.argument('keypath')
@click.pass_obj
def credentials(app_manager, file, keyspath):
    if not keyspath[0] == '/':
        keyspath = os.path.join(os.getcwd(), keyspath)
    config = Yaml(file)
    name = config.type
    for key, value in config.settings.items():
        print(f'export {(name + key).upper()}={value}')
    for key, value in config.certificates.items():
        key_path = os.path.join(keyspath, 'keys', value)
        print(f'export {(name + key).upper()}={key_path}')
