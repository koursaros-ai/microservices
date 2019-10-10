from kctl.logger import set_logger
import requests
import click
import json


@click.group()
@click.pass_context
def test(ctx):
    """Test a running pipeline"""


@test.command()
@click.argument('pipeline_name')
@click.pass_context
def pipeline(ctx, pipeline_name):
    logger = set_logger('TEST')

    if pipeline_name == 'telephone':
        url = 'http://localhost:5000/send'

        translations = dict(
            translations=[
                dict(lang='en',
                     text='I would love pancakes tomorrow morning'
                     )])

        logger.bold('Requesting %s on %s' % (translations, url))
        res = requests.post(url, data=translations)
        logger.bold(json.dumps(res, indent=4))
