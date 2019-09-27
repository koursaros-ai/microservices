from koursaros import Service
import os
import sys
sys.path.append(os.getcwd())
from utils.database.psql import Conn
import requests
import json

service = Service(__file__)


DBNAME = 'fever'
USER = 'postgres'
HOST = 'localhost'
PASSWORD = os.environ.get('PGPASS')
SSLMODE = 'verify-ca'
CERT_PATH = '/home/jp954/credentials/postgres.pem'
POSTGRES_HOST = '54.196.150.193'

HEADINGS = {"Content-Type": "application/json"}
MAPPINGS = {
    "mappings": {
        "properties": {
            "fever_id": {
                "type": "keyword"
            },
            "title": {
                "type": "text",
                "analyzer": "english"
            }
        }
    },
    "settings": {
        "index": {
            "number_of_shards": 5,
            "mapping.total_fields.limit": 100000
        }
    }
}

def fetch(method, uri, headers, body):
    request_func = getattr(requests, method, None)

    if request_func is None:
        raise AttributeError(f'requests has no attribute "{method}"')

    res = request_func(
        uri,
        headers=headers,
        data=json.dumps(body),
        stream=True
    )
    res.raise_for_status()
    return res.content


def es_multi_search(uri, index, headers, jsons):
    # jsons => json_id, json_body
    def set_index():
        return json.dumps({'index': index}) + '\n'

    json_ids = []
    body = set_index()
    for i, (json_id, json_body) in enumerate(jsons):
        json_ids.append(json_id)
        body += json.dumps(json_body) + '\n\n'

    res = fetch('post', uri, headers, body)

    return json_ids, json.loads(res).get('responses', [None])


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

# Elasticsearch connection
INDEX = 'titles'
ES_HOST = '34.70.112.177'
correct_fever_ids = dict()
HEADERS = {'Content-Type': 'application/json'}
FILTER_PATH = 'hits.hits._source.fever_id,responses.hits.hits._score'
BASE_URI = f'http://{ES_HOST}:9200/{INDEX}'
MSEARCH_URI = f'{BASE_URI}/_search?filter_path={FILTER_PATH}'


def apply_mapping(mapping):
    def request_status(method, *args, **kwargs):
        request_func = getattr(requests, method, None)
        res = request_func(*args, **kwargs)
        res = json.loads(res.content)
        acked = False if not res.get('acknowledged', True) else True
        no_errors = False if res.get('error', False) else True

        if acked and no_errors:
            print(res)
            return True
        else:
            print(res['error']['reason'])
            return False

    close_index_args = (f'{BASE_URI}/_close',)
    alter_index_args = (f'{BASE_URI}/_settings',)
    alter_index_kwargs = {'headers': HEADERS, 'data': json.dumps(mapping)}
    open_index_args = (f'{BASE_URI}/_open',)

    closed = request_status('post', *close_index_args)
    altered = request_status('put', *alter_index_args, **alter_index_kwargs)
    opened = request_status('post', *open_index_args)

def get_mapping():
    global HYPERS
    b = HYPERS['b']
    k1 = HYPERS['k1']
    x = HYPERS['x']
    y = HYPERS['y']
    z = HYPERS['z']

    weight_script = [
        f' double idf = (field.docCount - term.docFreq + 0.5) / (term.docFreq + 0.5);',
        f' double idfl = Math.log(idf) / Math.log({z});',
        f' return query.boost * idfl;'
    ]

    script = [
        f' double tf = Math.pow(doc.freq, 1 / {x});',
        f' double avgLen = field.sumTotalTermFreq / field.docCount;',
        f' double norm = Math.pow(1 - {b} + {b} * doc.length / avgLen, 1 / {y});',
        f' return weight * tf * ({k1} + 1) / (tf + {k1} * norm);'
    ]

    return {
        "settings": {
            "similarity": {
                "default": {
                    "type": "scripted",
                    "weight_script": {
                        "source": ' '.join(weight_script)
                    },
                    "script": {
                        "source": ' '.join(script)
                    }
                }
            },
        },
    }

def get_body(query):
    return {
        "size": ES_QUERY_RESULTS,
        "query": {
            "match": {
                "title": query
            }
        }
    }


# apply hyperparameters to elastic
apply_mapping(get_mapping())

@service.stub
def get_articles(claim, publish):

    body = get_body(claim.text)

    res = fetch('post', MSEARCH_URI, HEADERS, body)
    print(res)

    hits = json.loads(res)['hits']['hits']
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
    where a.fever_id in ({','.join(["'"+ fever_id + "'" for fever_id in fever_ids])})
    ''')
    lines = [row[0] for row in rows]
    results = service.messages.ClaimWithLines(
        claim=claim,
        lines=lines
    )
    print('publishing...')
    publish(results)


def main():
    threads = service.run()

    for t in threads:
        t.start()

    for t in threads:
        t.join()