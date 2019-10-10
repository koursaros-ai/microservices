from kctl.logger import set_logger
import requests
import click
import json


@click.group()
@click.pass_context
def test(ctx):
    """Test a running pipeline"""


def log_json_res(res):
    logger = set_logger('TEST')
    logger.info(json.dumps(json.loads(res.content), indent=4)
                .encode().decode("unicode_escape"))


@test.command()
@click.argument('pipeline_name')
@click.pass_context
def pipeline(ctx, pipeline_name):
    logger = set_logger('TEST')

    if pipeline_name == 'telephone':
        url = 'http://localhost:5000'
        headers = {'Content-Type': 'application/json'}

        translations = json.dumps({
            'translations': [{
                'lang': 'en',
                'text': input('What would you like to translate?\t') 
            }]
        })

        logger.bold('POSTING %s on %s' % (translations, url))
        res = requests.post(url + '/send', data=translations, headers=headers)
        log_json_res(res)
        logger.bold('REQ STATUS')
        res = requests.get(url + '/status', data=translations, headers=headers)
        log_json_res(res)
