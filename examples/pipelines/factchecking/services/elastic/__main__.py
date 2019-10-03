from koursaros.pipelines import factchecking
import os
import sys
sys.path.append(os.getcwd())
from ...utils.database.psql import Conn

import json


pipeline = factchecking(__file__)
elastic = pipeline.services.elastic
scorer = pipeline.services.scorer

DBNAME = 'fever'
USER = 'postgres'
HOST = 'localhost'
PASSWORD = os.environ.get('PGPASS')
SSLMODE = 'verify-ca'
CERT_PATH = os.environ.get('CERT_PATH')
POSTGRES_HOST = '54.196.150.193'

# Static Hypers
CLAIMS_PER_CHUNK = 30
ES_QUERY_RESULTS = 9
ES_THREADS = 5
APPLY_FAILURE_RETRY_DELAY = 5
SAMPLE_SIZE = 10000

HYPERS = {
    'type': 'scripted',
    'x': 4.954666662367618,
    'y': 1.5952138657439607,
    'z': 5.362376731750018,
    'b': 1.1615105837165731,
    'k1': 3.615698435281512
}


@elastic.stubs.retrieve
def get_articles(claim):

    fever_ids = [hit['_source']['fever_id'] for hit in hits]

    conn = Conn(
        host=POSTGRES_HOST,
        user=USER,
        password=PASSWORD,
        dbname=DBNAME,
        sslmode=SSLMODE,
        cert_path=CERT_PATH
    )

    rows = conn.query(f'''
    select l.text from wiki.lines l join wiki.articles a on l.article_id = a.id 
    where a.fever_id in ({','.join(["'"+ fever_id.replace("'","''") + "'" for fever_id in fever_ids])})
    ''')
    lines = [row[0] for row in rows]
    results = elastic.stubs.retrieve.ClaimWithLines(
        claim=claim,
        lines=lines
    )
    scorer.stubs.rerank(results)


if __name__ == "__main__":
    elastic.run()