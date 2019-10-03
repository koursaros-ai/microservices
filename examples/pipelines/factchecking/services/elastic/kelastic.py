
import requests
import json

HEADERS = {'Content-Type': 'application/json'}

MAPPINGS = '''
    {
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
'''

WEIGHT_SCRIPT = (
    ' double idf = (field.docCount - term.docFreq + 0.5) / (term.docFreq + 0.5);'
    ' double idfl = Math.log(idf) / Math.log({z});'
    ' return query.boost * idfl;'
)

SCRIPT = (
    ' double tf = Math.pow(doc.freq, 1 / {x});'
    ' double avgLen = field.sumTotalTermFreq / field.docCount;'
    ' double norm = Math.pow(1 - {b} + {b} * doc.length / avgLen, 1 / {y});'
    ' return weight * tf * ({k1} + 1) / (tf + {k1} * norm);'
)

VARIABLES = ['z', 'k1', 'x', 'b', 'y']

SETTINGS = '''
    {
        "settings": {
            "similarity": {
                "default": {
                    "type": "scripted",
                    "weight_script": {
                        "source": '{weight_script}'
                    },
                    "script": {
                        "source": '{script}'
                    }
                }
            },
        },
    }
'''

BODY = '''
    {
        "size": {size},
        "query": {
            "match": {
                "title": {query}
            }
        }
    }
'''


class RequestJsonFetcher:

    @classmethod
    def fetch(cls, method, uri, headers, body):
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
        return json.loads(res.content)


class Kelastic(RequestJsonFetcher):

    class KelasticError(Exception):
        pass

    def __init__(self,
                 host='localhost',
                 port='9200',
                 results=None,
                 filter_path=None,
                 index=None,
                 hypers=None
                 ):

        self._index = index
        self._base_uri = f'http://{host}:{port}/{index}'
        self._results = results
        self.hypers = hypers
        self._msearch_uri = f'{self._base_uri}/_search?filter_path={filter_path}'

    @staticmethod
    def d(json_, i):
        return json.dumps(json_, indent=i)

    def set_index(self):
        return self.d({'index': self._index}, 0) + '\n'

    def multisearch(self, uri, jsons):
        # jsons => json_id, json_body

        json_ids = []
        body = self.set_index()
        for i, (json_id, json_body) in enumerate(jsons):
            json_ids.append(json_id)
            body += json.dumps(json_body) + '\n\n'

        res = self.fetch('post', uri, HEADERS, body)

        return json_ids, res.get('responses', [None])

    def request_status(self, method, *args, **kwargs):
        res = self.fetch(method, *args, **kwargs)
        acked = res.get('acknowledged', True)
        no_errors = res.get('error', True)

        if acked and no_errors:
            print(self.d(res, 4))
            return True
        else:
            print(self.d(res['error']['reason'], 4))
            return False

    def apply_mapping(self, mapping):
        close_index_args = (f'{self._base_uri}/_close',)
        alter_index_args = (f'{self._base_uri}/_settings',)
        alter_index_kwargs = {'headers': HEADERS, 'data': self.d(mapping, 0)}
        open_index_args = (f'{self._base_uri}/_open',)

        closed = self.request_status('post', *close_index_args)
        altered = self.request_status('put', *alter_index_args, **alter_index_kwargs)
        opened = self.request_status('post', *open_index_args)

        print(closed)
        print(altered)
        print(opened)

    @staticmethod
    def list_is_in_dict(list_, dict_):
        return all(item in dict_ for item in list_)

    @staticmethod
    def filter_dict(list_, dict_):
        return {k: v for k, v in dict_ if k in list_}

    def get_settings(self):

        try:
            settings = SETTINGS.format(
                weight_script=WEIGHT_SCRIPT.format_map(**self.hypers),
                script=SCRIPT.format_map(**self.hypers)
            )
        except KeyError as exc:
            raise self.KelasticError(f'{exc}\nHypers {self.hypers} dont contain "{VARIABLES}"')

        return settings

    def get_hits(self, query):
        body = BODY.format(self._results, query)
        res = self.fetch('post', self._msearch_uri, HEADERS, body)
        return res['hits']['hits']