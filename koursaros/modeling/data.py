import csv

def get_rows_from_tsv(fname):
    if fname.split('.')[-1] == 'tsv':
        delimiter = '\t'
    else:
        delimiter = ','
    with open(fname) as file:
      return csv.reader(file, delimiter=delimiter)

def select_all(schema, table, random=True):
    query = f'select * from {schema}.{table}'
    if random:
        query += 'order by random()'
    return query