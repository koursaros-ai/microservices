from psycopg2 import extensions, extras
import os


def is_nested(nested):
    if any(not isinstance(i, (list, tuple)) for i in nested):
        raise ValueError('Hey dumbass - you can only dump nested lists/tuples.')


class Ksql(extensions.connection):
    def __init__(self,
                 host=None,
                 user=None,
                 password=None,
                 dbname=None,
                 sslmode=None,
                 cert_path=None
                 ):

        if sslmode:
            os.environ['PGSSLMODE'] = sslmode
        if cert_path:
            os.environ['PGSSLROOTCERT'] = cert_path
        dsn = f"dbname='{dbname}' user='{user}' host='{host}' password='{password}'"

        super(Ksql, self).__init__(dsn=dsn)

    def _set_columns(self, cur):
        self.columns = [desc.name for desc in cur.description]

    def execute(self, query):
        cur = self.cursor()
        cur.execute(query)

    def iter_rows(self, query):
        cur = self.cursor()
        cur.execute(query)
        self._set_columns(cur)
        return cur

    def iter_chunk(self, query, chunksize):
        cur = self.cursor()
        cur.execute(query)
        self._set_columns(cur)
        chunk = cur.fetchmany(chunksize)
        while chunk:
            yield chunk
            chunk = cur.fetchmany(chunksize)

    def query(self, query):
        cur = self.cursor()
        cur.execute(query)
        fetched = cur.fetchall()
        self._set_columns(cur)
        return fetched

    def insert(self, table, nested):
        is_nested(nested)
        cur = self.cursor()
        template = f'INSERT INTO {table} VALUES %s'
        extras.execute_values(cur, template, nested)

    def table_exists(self, schema, table):
        query = f'''
        SELECT EXISTS (
           SELECT
           FROM   information_schema.tables 
           WHERE  table_schema = '{schema}'
           AND    table_name = '{table}'
        );
        '''
        cur = self.cursor()
        cur.execute(query)
        return cur.fetchone()[0]

    def database_exists(self, database):
        query = f'''
        SELECT EXISTS (
            SELECT
            FROM pg_database
            WHERE datname = '{database}'
        )
        '''
        cur = self.cursor()
        cur.execute(query)
        return cur.fetchone()[0]

    def create_database(self, database):
        query = f'''
        COPY (SELECT 1) TO PROGRAM 'createdb {database}';
        '''
        cur = self.cursor()
        cur.execute(query)
