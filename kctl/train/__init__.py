import click
# from utils.train.roberta_inference import RobertaInference
import os
from shared.modeling import get_model

@click.command()
@click.argument('name')
@click.pass_obj
def train(pathmanager, name):
    model = get_model(name)
    model.train()

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    pass
