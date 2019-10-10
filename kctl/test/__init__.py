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
                'lang': 'en',
                'text': input('What would you like to translate?\t')
            }]
        })

        logger.bold('POSTING %s on %s' % (translations, url))
        res = requests.post(url, data=translations, headers=headers)
        res = json.loads(res.content)
        logger.info(json.dumps(res, indent=4))
        if 'error' in res:
            logger.info('error:\n%s' % res['error'].encode().decode("unicode_escape"))

        else:
            translations = ''
            for trans in res['translations']:
                translations += 'lang: %s\n trans: %s\n' % (trans['lang'], trans['text'])

            logger.info('Translations:\n%s' % translations)
