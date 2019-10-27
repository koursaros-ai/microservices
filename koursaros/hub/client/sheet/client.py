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
        self.mode = mode
        self.limit = limit
        if mode not in MODES:
            raise ValueError('%s is not valid. Please choose one of %s' % (mode, MODES))

        self.iter_csv(getattr(self, mode))

    def post(self, data):
        print('Posting:', data)
        response = requests.post('http://localhost:80/%s' % self.mode, data=data, headers=HEADERS)
        res = json.loads(response.content)
        if 'res' in res:
            self.result = json.loads(res['res'][0])
        else:
            self.result = res
        print('Returned:', self.result)

    def iter_csv(self, get_body_from_row):
        i = 0
        to_send = []
        for row in self.csv:
            to_send.append(get_body_from_row(row))
            if self.limit is not None and i > self.limit: break
            i += 1
        self.post('\n'.join(to_send).encode())

    def index(self, row):
        return list(row.values())[1]

    def train(self, row):
        return json.dumps(row, ensure_ascii=False)

    def query(self, row):
        return list(row.values())[0]

    def query_one(self, text):
        self.mode = 'query'
        response = self.post(text.encode)
        res = json.loads(response.content)
        self.result = json.loads(res['res'][0])
        return self.text()

    def text(self):
        return self.result['search']['topkResults'][0]['doc']['chunks'][0]['text']