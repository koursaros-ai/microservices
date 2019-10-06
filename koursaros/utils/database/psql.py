from psycopg2 import extensions, extras, pool
import sys, time, os
# from psutil import cpu_percent, virtual_memory
from threading import Thread, Lock
from multiprocessing import cpu_count, Queue, Process, Value, Condition


def is_nested(nested):
    if any(not isinstance(i, (list, tuple)) for i in nested):
        raise ValueError('Hey dumbass - you can only dump nested lists/tuples.')


class Conn(extensions.connection):
    def __init__(self, host=None, user=None, password=None, dbname=None, sslmode=None, cert_path=None):
        if sslmode:
            os.environ['PGSSLMODE'] = sslmode
        if cert_path:
            os.environ['PGSSLROOTCERT'] = cert_path
        if not host:
            host = os.environ.get('PGHOST')
        if not user:
            user = os.environ.get('PGUSER')
        if not password:
            password = os.environ.get('PGPASS')
        if not dbname:
            dbname = os.environ.get('PGDBNAME')
        dsn = f"dbname='{dbname}' user='{user}' host='{host}' password='{password}'"
        super(Conn, self).__init__(dsn=dsn)

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


class PolomaBuff:
    def __init__(self,
                 table,
                 workers=cpu_count(),
                 maxconn=cpu_count(),
                 maxbuff=50000,
                 batchsize=5000,
                 *args, **kwargs):

        self.table = table
        self.maxbuff = maxbuff
        self.maxconn = maxconn
        self.batchsize = batchsize
        self._args = args
        self._kwargs = kwargs
        self._queue = Queue()
        self._buffer_notifier = Condition()
        self._conn_notifier = Condition()
        self._conns = Value('i', 0)
        self._buffsize = Value('i', 0)
        self._sent = Value('i', 0)
        self._workers = 0
        self._buffer = []
        self._procs = []
        self._spawn(workers)
        self._progress()

    def _progress(self):
        print('\tSENT:', self._sent.value,
              'BUFFER:', self._buffsize.value,
              'CONNS:', self._conns.value,
              'WORKERS:', self._workers,
              ' ' * 10, end='\r')

    def _spawn(self, workers):
        for _ in range(workers):
            values = (self._sent,
                      self._buffsize,
                      self._conns,
                      self._queue,
                      self._buffer_notifier,
                      self._conn_notifier)
            p = Process(target=self._worker, args=values)
            p.daemon = True
            self._procs.append(p)
            p.start()
            self._workers += 1

    def _worker(self, _sent,
                _buffsize, _conns,
                _queue, _buffer_notifier,
                _conn_notifier):

        def _wait_if_max_conns():
            _conn_notifier.acquire()
            while _conns.value >= self.maxconn:
                _conn_notifier.wait()
            _conn_notifier.release()

        def _send(_conn_notifier, _conns, _sent, _buffer):
            _conns.value += 1
            c = Conn(*self._args, **self._kwargs)
            is_nested(_buffer)
            c.insert(self.table, _buffer)
            c.commit()
            c.close()
            _conns.value -= 1
            _notify(_conn_notifier)
            _sent.value += len(_buffer)

        def _notify(notifier):
            notifier.acquire()
            notifier.notify()
            notifier.release()

        while True:
            _buffer = _queue.get()
            _buffsize.value -= len(_buffer)
            _notify(_buffer_notifier)
            if _buffer == 'KILL':
                break
            _wait_if_max_conns()
            Thread(target=_send, args=(_conn_notifier, _conns, _sent, _buffer)).start()

    def _wait_if_buff_full(self):
        self._buffer_notifier.acquire()
        while self._buffsize.value >= self.maxbuff:
            self._buffer_notifier.wait()
        self._buffer_notifier.release()

    def append(self, item, batch=False):
        if batch:
            self._buffer += item
        else:
            self._buffer.append(item)

        self._wait_if_buff_full()

        if len(self._buffer) >= self.batchsize:
            self._buffsize.value += len(self._buffer)
            self._queue.put(self._buffer)
            self._progress()
            self._buffer = []

    def kill(self):
        for _ in range(self._workers):
            self._queue.put('KILL')
        for p in self._procs:
            p.join()
            print()
