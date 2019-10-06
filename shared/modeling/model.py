import csv
import hashlib
import os
from shared.utils.database.psql import Conn

def get_rows_from_tsv(fname):
    samples = []
    with open(fname) as file:
      return csv.reader(file, delimiter='\t')

def select_all(table):
    return f'select * from {table} order by random()'

class Model(object):

    def __init__(self, config, version):
        # load configs from yaml
        self.config = config
        self.version = version
        ckpt_path = f'.cache/{version}.bin'
        if os.path.exists(ckpt_path): # else check if in model repo
            self.checkpoint = ckpt_path
            self.trained = True
        else:
            self.checkpoint = config.training.checkpoint
            self.trained = False

    # train_data and test_data are either URL to download from
    # conn.query_fn = (query) -> of form text1, <optional text2>, label
    # returns train_data, test data iterable of rows
    def get_data(self):
        data = self.config.data
        if data.source == 'postgres':

            p = Conn(
                host=os.environ.get('PGHOST'),
                user=os.environ.get('PGUSER'),
                password=os.environ.get('PGPASS'),
                dbname=os.environ.get('PGDBNAME'),
                sslmode=os.environ.get('PGSSLMODE')
            )
            query_fn = p.query
            return query_fn(select_all(train_data)), query_fn(select_all(test_data))
        else:
            return get_rows_from_tsv(train_data), get_rows_from_tsv(test_data)

    # train_data and test_data both lists of rows
    def train(self):
        # CHECK TO MAKE SURE DEVICE HAS ENOUGH SPACE
        raise NotImplementedError()

    def run(self, *args):
        raise NotImplementedError()

    def save_model(self):
        # append hash of yaml to model checkpoint
        raise NotImplementedError()

    @staticmethod
    def architectures():
        raise NotImplementedError()

