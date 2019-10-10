from koursaros.modeling import model_from_yaml
import sys, os
from koursaros.utils.database.psql import Conn
from koursaros.utils.misc import batch_list
from koursaros.modeling.data import *
import csv

BATCH_SIZE = int(os.environ.get('BATCH_SIZE') or 4)

def predict(model_file, data_source, data_target):
    model = model_from_yaml(model_file)
    extension = data_source.split('.')[-1]
    if extension in ['tsv', 'csv']:
        rows = get_rows_from_tsv(data_source)
        delimiter = '\t' if extension == 'tsv' else 'csv'
        open(data_target, 'w+') # touch file

        def write_fn(buffer):
            file = open(data_target, 'a')
            writer = csv.writer(file, delimiter=delimiter)
            for row in buffer: writer.writerow(row)

    else:
        p = Conn()
        query_fn = p.query
        schema, table = data_source.split('.')
        rows = query_fn(select_all(schema, table, random=False))

        def write_fn(buffer):
            p.insert(data_target, buffer)
            p.commit()

    buffer = []
    i = 0
    for batch in batch_list(rows, BATCH_SIZE):
        import pdb
        pdb.set_trace()
        buffer.extend(zip(*(batch[-1], model.run(*zip(*batch[:-1])))))
        i += BATCH_SIZE
        if BATCH_SIZE > 1000:
            write_fn(buffer)
            buffer = []

    if len(buffer) > 0: write_fn(buffer)

if __name__ == '__main__':
    model_file = sys.argv[1]
    data_source = sys.argv[2]
    data_target = sys.argv[3] if len(sys.argv) > 3 else './predictions.tsv'
    predict(model_file, data_source, data_target)