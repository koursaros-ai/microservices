import requests
import pathlib
import csv
import json

HEADERS = {'Content-Type': 'application/json'}
MODES = ['index', 'train', 'query']


class Client:

    def __init__(self, mode, path, limit=None):
        self.path = pathlib.Path(path)
        self.csv = csv.DictReader(self.path.open())
        self.limit = limit
        if mode not in MODES:
            raise ValueError('%s is not valid. Please choose one of %s' % (mode, MODES))

        self.iter_csv(getattr(self, mode))

    @staticmethod
    def post(data, method):
        print('Posting:', data)
        response = requests.post('http://localhost:80/%s' % method, data=data, headers=HEADERS)
        res = json.loads(response.content)['res'][0]
        result = json.loads(res)
        print('Returned:', result)

    def iter_csv(self, fn):
        i = 0
        for row in self.csv:
            fn(row)
            if self.limit is not None and i > self.limit: break
            i += 1

    def index(self, row):
        self.post(list(row.values())[1].encode(), 'index')

    def train(self, row):
        self.post(json.dumps(row, ensure_ascii=False).encode(), 'train')

    def query(self, row):
        self.post(list(row.values())[0].encode(), 'query')