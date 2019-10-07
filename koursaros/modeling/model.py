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

    def __init__(self, config):
        # load configs from yaml
        if gb_free_space() < 2:
            print("There is not enough space on your disk, please allocate more!")
            raise SystemError

        self.config = config
        self.version = config.hash
        self.ckpt_dir = f'.cache/{self.version}/'
        if os.path.exists(self.ckpt_dir + 'config.json') or not 'training' in self.config:
            self.checkpoint = self.ckpt_dir
            self.trained = True
        else:
            self.data_dir = os.path.join('.model-data', self.version)
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            if not os.path.exists(self.ckpt_dir):
                os.makedirs(self.ckpt_dir)
            self.checkpoint = config.training.checkpoint
            self.trained = False

    # train_data and test_data are either URL to download from
    # conn.query_fn = (query) -> of form text1, <optional text2>, label
    # returns train_data, test data iterable of rows
    def get_data(self):
        """
        Get training data based on yaml config and connection
        :return:
        """
        data = self.config.training.data
        if data.source == 'postgres':
            p = Conn()
            query_fn = p.query
            return query_fn(select_all(data.schema, data.train)), \
                   query_fn(select_all(data.schema, data.test))
        else:
            return get_rows_from_tsv(data.train), get_rows_from_tsv(data.test)

    # train_data and test_data both lists of rows
    def train(self):
        """
        Runs training as defined in the model yaml. Saves model to directory
        .cache/<md5 hash of yaml>
        :return: evaluation metric
        """
        raise NotImplementedError()

    def run(self, *args):
        """
        Runs inference on arbitrary args
        :param args: sent_a, sent_b for classification / regression task.
        :return:
        """
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

