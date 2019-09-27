from .helpers import *


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
FILTER_PATH = 'responses.hits.hits._source.fever_id,responses.hits.hits._score'
BASE_URI = f'http://{ES_HOST}:9200/{INDEX}'
MSEARCH_URI = f'{BASE_URI}/_msearch?filter_path={FILTER_PATH}'


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

    while True:
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
