
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


def SETTINGS(weight_script=None, script=None):
    return {
        "settings": {
            "similarity": {
                "default": {
                    "type": "scripted",
                    "weight_script": {
                        "source": weight_script
                    },
                    "script": {
                        "source": script
                    }
                }
            },
        },
    }


def BODY(size=None,query=None):
    return {
        "size": size,
        "query": {
            "match": {
                "title": query
            }
        }
    }


class RequestJsonFetcher:

    @staticmethod
    def fetch(method, uri, headers=None, body=None):
        request_func = getattr(requests, method, None)

        if request_func is None:
            raise AttributeError(f'requests has no attribute "{method}"')

        req = {'stream': True}
        if headers:
            req['headers'] = headers
        if body:
            req['data'] = body

        res = request_func(uri, **req)
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
        self._msearch_uri = f'{self._base_uri}/_msearch?filter_path={filter_path}'

    @staticmethod
    def d(json_, i):
        return json.dumps(json_)

    def set_index(self):
        return self.d({'index': self._index}, 0) + '\n'

    def multisearch(self, uri, jsons):
        # jsons => json_id, json_body

        json_ids = []
        body = self.set_index()
        for i, (id_, json_) in enumerate(jsons):
            json_ids.append(id_)
            body += json.dumps(json_) + '\n\n'

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

    def apply_settings(self, mapping):
        close_index_args = (f'{self._base_uri}/_close',)
        alter_index_args = (f'{self._base_uri}/_settings',)
        alter_index_kwargs = {'headers': HEADERS, 'body': self.d(mapping, 0)}
        open_index_args = (f'{self._base_uri}/_open',)
        print('post', *close_index_args)
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
            settings = SETTINGS(
                weight_script=WEIGHT_SCRIPT.format_map(self.hypers),
                script=SCRIPT.format_map(self.hypers)
            )
        except KeyError as exc:
            raise self.KelasticError(f'{exc}\nHypers {self.hypers} dont contain "{VARIABLES}"')

        return settings

    def get_hits(self, queries):
        # self.apply_settings(self.get_settings())
        bodies = [[id_, BODY(size=self._results, query=query)] for id_, query in queries]

        ids, res = self.multisearch(self._msearch_uri, bodies)
        return ids, res


