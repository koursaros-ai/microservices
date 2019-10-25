import requests
from tabulate import tabulate
import pathlib
import pandas as pd
import os
import json
import time

HEADERS = {'Content-Type': 'application/json'}


class Client:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.df = pd.read_csv(self.path)
        self.cols = len(self.df.columns)
        self.height, self.width = self.terminal_width

    @property
    def terminal_width(self):
        try:
            return os.get_terminal_size(0)
        except OSError:
            return os.get_terminal_size(1)

    def run(self):
        print(tabulate(
            self.df.head(round(self.height / 25))
                .astype(str)
                .apply(lambda x: x.str[:round(self.height/self.cols)]),
            headers='keys',
            tablefmt='fancy_grid')
        )

        print('\n'.join('\t%s) %s' % (k, v) for k, v in zip(
            range(self.cols), self.df.columns)))

        try:
            col_names = input('Json keys? ').strip().replace(' ', '').split(',')
            cols = dict.fromkeys(col_names, 1)
            for col in cols:
                cols[col] = self.df.iloc[:, [int(input('Which column is "%s"? ' % col))]]

        except Exception as ve:
            print('Invalid input:', ve)
            raise SystemExit

        while True:
            for i in [1]:
                j = json.dumps({col_name: str(col.iloc[i].values[0]) for col_name, col in cols.items()})
                time.sleep(2)
                print('Sending:', j)
                res = requests.post('http://localhost:80/train', data=j, headers=HEADERS)
                print('Returned:', res.content)

            input('Again?')
