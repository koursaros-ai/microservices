import csv
import hashlib
import os
from koursaros.utils.database.psql import Conn
from koursaros.utils.misc import gb_free_space

def get_rows_from_tsv(fname):
    samples = []
    with open(fname) as file:
      return csv.reader(file, delimiter='\t')

def select_all(schema, table):
    return f'select * from {schema}.{table} order by random()'

class Model(object):

    def __init__(self, config, version):
        # load configs from yaml
        if gb_free_space() < 2:
            print("There is not enough space on your disk, please allocate more!")
            raise SystemError

        self.config = config
        self.version = version
        self.ckpt_dir = f'.cache/'
        self.ckpt_path = f'.cache/{version}.bin'
        self.data_dir = os.path.join('.model-data', self.version)
        if os.path.exists(self.ckpt_path): # else check if in model repo
            self.checkpoint = self.ckpt_path
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
            p = Conn()
            query_fn = p.query
            return query_fn(select_all(data.schema, data.train)), query_fn(select_all(data.schema, data.test))
        else:
            return get_rows_from_tsv(data.train), get_rows_from_tsv(data.test)

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

    def getInputProto(self):
        raise NotImplementedError()

    def getOutputProto(self):
        raise NotImplementedError()
