import requests
import json

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
        data=body,
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
