from koursaros.pipelines import factchecking
from .ksql import Ksql
from .kelastic import Kelastic
import os

pipeline = factchecking(__package__)

elastic = pipeline.Services.elastic
scorer = pipeline.Services.scorer

ES_HYPERS = {
    'x': 4.954666662367618,
    'y': 1.5952138657439607,
    'z': 5.362376731750018,
    'b': 1.1615105837165731,
    'k1': 3.615698435281512
}

QUERY_CLAIM_IDS = '''
    SELECT l.text
    FROM wiki.lines l
    JOIN wiki.articles a
        ON l.article_id = a.id 
    WHERE a.fever_id IN ({ids})
'''

# Elasticsearch connection
kelastic = Kelastic(
    host='34.70.112.177',
    index='titles',
    results=40,
    filter_path='hits.hits._source.fever_id,responses.hits.hits._score'
)

# Postgres connection
ksql = Ksql(
    host='54.196.150.193',
    user='postgres',
    password=os.environ.get('PGPASS'),
    dbname='fever',
    sslmode='verify-ca',
    cert_path=os.environ.get('CERT_PATH')
)


@elastic.Stubs.retrieve
def get_articles(claim):
    hits = kelastic.get_hits(claim)
    fever_ids = [hit['_source']['fever_id'] for hit in hits]
    fever_ids = ','.join(["'" + fever_id.replace("'", "''") + "'" for fever_id in fever_ids])

    rows = ksql.query(
        QUERY_CLAIM_IDS.format(fever_ids)
    )

    lines = [row[0] for row in rows]
    results = elastic.Stubs.retrieve.ClaimWithLines(
        claim=claim,
        lines=lines
    )
    return results


def send_claims():
    query = '''
        SELECT text
        FROM sets.claims
        LIMIT 10;
    '''
    claims = ksql.query(query)
    print(claims)


if __name__ == "__main__":
    elastic.run()
    send_claims()
    elastic.join()
