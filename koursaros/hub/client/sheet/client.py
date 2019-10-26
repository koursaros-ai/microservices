import requests
import pathlib
import csv
import json

HEADERS = {'Content-Type': 'application/json'}
MODES = ['index', 'train', 'query']


class Client:

    def __init__(self, mode, path):
        self.path = pathlib.Path(path)
        self.csv = csv.DictReader(self.path.open())
        if mode not in MODES:
            raise ValueError('%s is not valid. Please choose one of %s' % (mode, MODES))

        getattr(self, mode)()

    @staticmethod
    def post(data, method):
        print('Posting:', data)
        res = requests.post('http://localhost:80/%s' % method, data=data, headers=HEADERS)
        print('Returned:', res.content)

    def index(self):
        for row in self.csv:
            self.post(list(row.values())[0], 'index')

    def train(self):
        for row in self.csv:
            self.post(json.dumps(row), 'train')

    def query(self):
        for row in self.csv:
            self.post(list(row.values())[0], 'query')