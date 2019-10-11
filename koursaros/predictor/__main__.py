from koursaros.modeling import model_from_yaml
import sys, os
from koursaros.utils.database.psql import Conn
from koursaros.utils.misc import batch_list
from koursaros.modeling.data import *
import csv
import time
import torch

BATCH_SIZE = int(os.environ.get('BATCH_SIZE') or 4)

def predict(model_file, data_source, data_target, truncate=False):
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
        if truncate:
            p.execute(f'''truncate table {data_target}''')
        rows = query_fn(select_all(schema, table, random=False))

        def write_fn(buffer):
            p.insert(data_target, buffer)
            p.commit()

    buffer = []
    i = 0
    start = time.time()
    for step, batch in enumerate(batch_list(rows, BATCH_SIZE)):
        transposed = tuple(zip(*batch))
        inputs = transposed[:2]
        ids = transposed[2:]
        buffer.extend(zip(*ids, model.run(*inputs)))
        i += BATCH_SIZE
        if i > 500:
            total = step * BATCH_SIZE
            print('dumping example {}, rate: {} per second'.format(total, total/(time.time() - start)))
            write_fn(buffer)
            buffer = []
            i = 0

    if len(buffer) > 0: write_fn(buffer)

if __name__ == '__main__':
    model_file = sys.argv[1]
    data_source = sys.argv[2]
    data_target = sys.argv[3] if len(sys.argv) > 3 else './predictions.tsv'
    truncate = len(sys.argv) > 4 and sys.argv[4] == '-t'
    predict(model_file, data_source, data_target, truncate=truncate)