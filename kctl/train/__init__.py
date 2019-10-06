import click
# from utils.train.roberta_inference import RobertaInference
import os
# from koursaros.modeling import get_model
import transformers

@click.command()
@click.argument('name')
@click.pass_obj
def train(pathmanager, name):
    # model = get_model(name)
    # model.train()
    pass

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    pass
