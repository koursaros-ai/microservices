
import requests
import json


# Elasticsearch connection
INDEX = 'titles'
ES_HOST = '34.70.112.177'
correct_fever_ids = dict()
FILTER_PATH = 'hits.hits._source.fever_id,responses.hits.hits._score'
BASE_URI =
MSEARCH_URI = f'{BASE_URI}/_search?filter_path={FILTER_PATH}'
HEADERS = {'Content-Type': 'application/json'}
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

    def __init__(self, host='localhost', port='9200', index=None, hypers=None):
        self._index = index
        self._base_uri = f'http://{host}:{port}/{index}'
        self.hypers = hypers

    @staticmethod
    def dump(json_, i):
        return json.dumps(json_, indent=4)

    def set_index(self):
        return json.dumps({'index': self._index}) + '\n'

    def multisearch(self, uri, index, headers, jsons):
        # jsons => json_id, json_body

        json_ids = []
        body = self.set_index()
        for i, (json_id, json_body) in enumerate(jsons):
            json_ids.append(json_id)
            body += json.dumps(json_body) + '\n\n'

        res = self.fetch('post', uri, headers, body)

        return json_ids, json.loads(res).get('responses', [None])

    def request_status(self, method, *args, **kwargs):
        res = self.fetch(method, *args, **kwargs)
        acked = res.get('acknowledged', True)
        no_errors = res.get('error', True)

        if acked and no_errors:
            print(self.dump(res, 4))
            return True
        else:
            print(self.dump(res['error']['reason'], 4))
            return False

    def apply_mapping(self, mapping):
        close_index_args = (f'{self._base_uri}/_close',)
        alter_index_args = (f'{self._base_uri}/_settings',)
        alter_index_kwargs = {'headers': HEADERS, 'data': self.dump(mapping, 0)}
        open_index_args = (f'{self._base_uri}/_open',)

        closed = self.request_status('post', *close_index_args)
        altered = self.request_status('put', *alter_index_args, **alter_index_kwargs)
        opened = self.request_status('post', *open_index_args)


    def check_dict(self, dict_, list_):
        if all(item in dict_ for item in list_):


    def get_mapping(self):
        vars().update(self.hypers)

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