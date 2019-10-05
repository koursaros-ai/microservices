import csv

def get_rows_from_tsv(fname):
    samples = []
    with open(fname) as file:
      return csv.reader(file, delimiter='\t')

def select_all(table):
    return f'select * from {table} order by random()'

class Model(object):

    def __init__(self):
        # load configs from yaml
        self.data_loader = None # self.get_data_loader(configs)
        self.hash = None # Map to hash of yaml
        self.architecture = None
        self.task = None
        self.lr = 1e-05
        pass

    # train_data and test_data are either URL to download from
    # conn.query_fn = (query) -> of form text1, <optional text2>, label
    # returns train_data, test data iterable of rows
    def get_data(self):
        if self.query_fn == None:
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
    def architectures(self):
        raise NotImplementedError()

