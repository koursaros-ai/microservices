import requests
from tabulate import tabulate
import pathlib
import pandas as pd
import os
import json
from typing import Iterable, List

HEADERS = {'Content-Type': 'application/json'}
OPTIONS = dict(error_bad_lines=False)


class Client:

    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.df = pd.read_csv(self.path, encoding='UTF-8', **OPTIONS)

    @property
    def terminal(self):
        try:
            return os.get_terminal_size(0)
        except OSError:
            return os.get_terminal_size(1)

    def print_table(self):
        height, width = self.terminal
        print(tabulate(
            self.df.head(round(height / 25))
                .astype(str)
                .apply(lambda x: x.str[:round(width/len(self.df))]),
            headers='keys',
            tablefmt='fancy_grid')
        )

    @staticmethod
    def print_options(options: Iterable):
        print('\n'.join('\t%s) %s' % (k, v) for k, v in enumerate(options)))

    @staticmethod
    def get_parsed_input(question: str) -> List[str]:
        return input(question).strip().replace(' ', '').split(',')

    def get_input_options(self, question: str, options: Iterable) -> List[int]:
        """returns the value matching the chosen key"""
        options = list(options)
        self.print_options(options)
        return [options[int(i)] for i in self.get_parsed_input(question)]

    @staticmethod
    def post(data):
        print('Posting:', data)
        method = 'index'
        res = requests.post('http://localhost:80/%s' % method, data=data, headers=HEADERS)
        print('Returned:', res.content)

    def bytesmode(self):
        self.print_table()
        col = self.get_input_options('Which column?', self.df.columns)[0]

        for row in self.df[col]:
            self.post(row.encode('utf-8'))

    def jsonmode(self):
        keys = self.get_parsed_input('Json keys? ')
        self.print_table()
        print(', '.join(keys))
        cols = self.get_input_options('Which columns for "%s"?' % ', '.join(keys), self.df.columns)

        print([self.df[col] for col in cols])
        quit()
        for rows in pd.DataFrame([self.df[col] for col in cols]).iterrows():
            print(rows)
            # self.post(dict(zip(cols, rows)))

    def run(self):
        # try:
        question = 'Mode?'
        options = dict(
            bytes=self.bytesmode,
            json=self.jsonmode
        )
        options[self.get_input_options(question, options.keys())[0]]()

        # except Exception as ve:
        #     print('%s:' % self.path.absolute(), ve)
        #     raise SystemExit

import sys
Client(sys.argv[1]).run()