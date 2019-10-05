import click
# from utils.train.roberta_inference import RobertaInference
import os
from shared.modeling import model_from_yaml

@click.command()
@click.pass_obj
def train(*args):
    name = args[0]
    load_model
    model_from_yaml(name)

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    main(*args)
