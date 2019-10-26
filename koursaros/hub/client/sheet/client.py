import requests
import pathlib
import csv
import json

HEADERS = {'Content-Type': 'application/json'}
MODES = ['json', 'bytes']


class Client:

    def __init__(self, mode, path):
        self.path = pathlib.Path(path)
        self.csv = csv.DictReader(self.path.open())
        if mode not in MODES:
            raise ValueError('%s is not valid. Please choose one of %s' % (mode, MODES))

        getattr(self, mode)()

    @staticmethod
    def post(data):
        print('Posting:', data)
        method = 'index'
        res = requests.post('http://localhost:80/%s' % method, data=data, headers=HEADERS)
        print('Returned:', res.content)

    def bytes(self):
        for row in self.csv:
            self.post(list(row.values())[0])

    def json(self):
        for row in self.csv:
            self.post(json.dumps(row))