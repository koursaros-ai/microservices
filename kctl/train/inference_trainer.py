import csv

def get_rows_from_tsv(fname):
    samples = []
    with open(fname) as file:
      return csv.reader(file, delimiter='\t')

def select_all(table):
    return f'select * from {table} order by random()'

class InferenceTrainer(object):

    # train_data and test_data are either URL to download from
    # conn.query_fn = (query) -> of form text1, <optional text2>, label
    # returns train_data, test data iterable of rows
    def get_data(self, train_data, test_data, from_db=True, query_fn=None):
        if from_db == True:
            if query_fn == None:
                print('Please specify a query_fn or set from_db to False!')
                raise NotImplementedError()
            return query_fn(select_all(train_data)), query_fn(select_all(test_data))
        else:
            return get_rows_from_tsv(train_data), get_rows_from_tsv(test_data)


    # train_data and test_data both lists of rows
    def train(self, train_data, test_data, checkpoint):
        raise NotImplementedError()

    def save_model(self, output_bucket):
        raise NotImplementedError()




