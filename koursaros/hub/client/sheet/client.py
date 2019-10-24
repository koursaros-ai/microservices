import requests
import json
from tabulate import tabulate
import pathlib
import pandas as pd
import os


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
            data_col = self.df.iloc[:, [int(input('Data column? '))]]
            label_col = self.df.iloc[:, [int(input('Label column? '))]]
        except Exception as ve:
            print('Invalid input:', ve)
            raise SystemExit

        d = lambda x, y: str(x.iloc[y].values[0])

        for i in range(len(self.df)):
            dump = json.dumps({
                'docs': {
                    'data': d(data_col, i),
                    'label': d(label_col, i)
                }
            })
            
            res = requests.post('http://localhost:80/index', data=dump)
            import pdb; pdb.set_trace()

