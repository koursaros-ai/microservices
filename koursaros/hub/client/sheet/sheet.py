import requests
import json
from tabulate import tabulate
import sys
import pathlib
import pandas as pd
import os


class SheetClient:
    def __init__(self):
        if len(sys.argv) < 2:
            print('Please specify file path...')
            raise SystemExit

        self.path = pathlib.Path(sys.argv[1])
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
            dump = json.dumps(dict(
                data=d(data_col, i),
                label=d(label_col, i)
            ))
            print(dump)


if __name__ == '__main__':
    SheetClient().run()