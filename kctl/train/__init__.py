import click
# from utils.train.roberta_inference import RobertaInference
import os
from shared.modeling import get_model

@click.command()
@click.argument('name')
@click.pass_obj
def train(pathmanager, name):
    get_model(name)

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    pass
