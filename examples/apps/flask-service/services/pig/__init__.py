from koursaros import Service
import requests
import json
import time
from .elastic import *

service = Service(__file__)

# apply hyperparameters to elastic
apply_mapping(get_mapping())

@service.stub
def piggify(claim, publish):

    body = get_body(claim)
    buffer = [(0, body)]

    json_ids, responses = es_multi_search(MSEARCH_URI, INDEX, HEADERS, buffer)
    response = responses[0]

    hits = response['hits']['hits']
    fever_ids = [hit['_source']['fever_id'] for hit in hits]

    piggified = service.messages.Piggified(
        sentence=claim,
        pig_latin=' '.join(fever_ids)
    )
    publish(piggified)


def main():
    threads = service.run()

    for t in threads:
        t.start()

    for t in threads:
        t.join()