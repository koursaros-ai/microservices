from kctl.logger import set_logger
import requests
import click
import json
import ast

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
        headers = {'Content-Type': 'application/json'}

        translations = json.dumps({
            'translations': [{
                'src_lang': 'en',
                'text': 'I would love pancakes tomorrow morning'
            }]
        })

        logger.bold('POSTING %s on %s' % (translations, url))
        res = requests.post(url, data=translations, headers=headers)
        res = json.loads(res.content)
        logger.info(json.dumps(res, indent=4))
        if 'error' in res:
            logger.info('error:\n%s' % res['error'].encode().decode("unicode_escape"))
