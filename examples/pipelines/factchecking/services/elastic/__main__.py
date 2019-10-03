# from koursaros.pipelines import factchecking
from .ksql import Ksql
from .kelastic import Kelastic
import os

# pipeline = factchecking(__package__)

# elastic = pipeline.Services.elastic
# scorer = pipeline.Services.scorer

SCHEMA = 'test'
TABLE = 'elastic_50'
DUMP_SIZE = 1000
CHUNK_SIZE = 100
CREATE = f'''CREATE TABLE {SCHEMA}.{TABLE} (
    claim_id BIGINT PRIMARY KEY,
    fever_ids TEXT[] NOT NULL,
    scores DOUBLE PRECISION[] NOT NULL
)

'''


ES_HYPERS = {
    'x': 4.954666662367618,
    'y': 1.5952138657439607,
    'z': 5.362376731750018,
    'b': 1.1615105837165731,
    'k1': 3.615698435281512
}

# QUERY_CLAIM_IDS = '''
#     SELECT l.text
#     FROM wiki.lines l
#     JOIN wiki.articles a
#         ON l.article_id = a.id
#     WHERE a.fever_id IN ({ids})
# '''

# Elasticsearch connection
kelastic = Kelastic(
    host='34.70.112.177',
    index='titles',
    results=50,
    hypers=ES_HYPERS,
    filter_path='responses.hits.hits._source.fever_id,responses.hits.hits._score'
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


# @elastic.Stubs.retrieve
def get_articles(chunk):
    ids, hits = kelastic.get_hits(chunk)
    all_hits = [hit['hits']['hits'] for hit in hits]
    fever_ids = [[hit['_source']['fever_id'] for hit in hits] for hits in all_hits]
    scores = [[hit['_score'] for hit in hits] for hits in all_hits]
    # fever_ids = ','.join(["'" + fever_id.replace("'", "''") + "'" for fever_id in fever_ids])

    # rows = ksql.query(
    #     QUERY_CLAIM_IDS.format(fever_ids)
    # )

    # lines = [row[0] for row in rows]
    # results = elastic.Stubs.retrieve.ClaimWithLines(
    #     claim=claim,
    #     lines=lines
    # )
    return zip(ids, fever_ids, scores)


def send_claims():
    query = '''
        SELECT id, claim
        FROM sets.claims;
    '''

    if ksql.table_exists(SCHEMA, TABLE):
        ksql.execute(f'DROP TABLE {SCHEMA}.{TABLE};')
        ksql.commit()
        ksql.execute(CREATE)
        ksql.commit()
    else:
        ksql.execute(CREATE)
        ksql.commit()

    buffer = []
    for i, chunk in enumerate(ksql.iter_chunk(query, chunksize=CHUNK_SIZE)):
        for id_, fever_ids, scores in get_articles(chunk):
            buffer.append((id_, fever_ids, scores))

            if i and i % DUMP_SIZE == 0:
                ksql.insert(SCHEMA + '.' + TABLE, buffer)
                ksql.commit()
                buffer.clear()
            print(f'Dumped {i * CHUNK_SIZE} claims')
    if len(buffer) > 0:
        ksql.insert(SCHEMA + '.' + TABLE, buffer)
        ksql.commit()


if __name__ == "__main__":
    # elastic.run()
    send_claims()
    # elastic.join()
