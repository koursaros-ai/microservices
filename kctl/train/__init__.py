import click
# from utils.train.roberta_inference import RobertaInference
import os

@click.command()
@click.pass_obj
def train(*args):
    """Save current directory's pipeline"""
    main(*args)

@click.command()
@click.pass_obj
def eval(*args):
    """Save current directory's pipeline"""
    main(*args)

def main(args):
    pass
