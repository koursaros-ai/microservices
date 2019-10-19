from gnes.cli.parser import set_client_cli_parser
from koursaros.credentials import get_creds
from gnes.client.cli import CLIClient
from gnes.base import TrainableBase
import psycopg2
import json
import os

VALID_MODES = ['json', 'raw']


class PostgresClient(CLIClient):

    @property
    def bytes_generator(self):
        try:
            args = self.args
            creds = get_creds(args.git_dsn)

            psql = creds.postgres
            os.environ['PGSSLMODE'] = psql.sslmode
            os.environ['PGSSLROOTCERT'] = psql.sslrootcert.path

            columns = ', '.join([args.id_column] + args.data_columns)
            query = '''SELECT %s FROM %s''' % (columns, args.table)
            query += ' LIMIT %d' % args.limit if args.limit > 0 else ''
            query += ' ORDER BY %s DESC' % args.id_column

            connection = psycopg2.connect(user=psql.username,
                                          password=psql.password,
                                          host=psql.host,
                                          port=psql.port,
                                          dbname=psql.dbname)
            cursor = connection.cursor()
            cursor.execute(query)

            if args.mode not in VALID_MODES:
                raise ValueError('"mode" parameter must be one of %s' % VALID_MODES)
            else:
                for i, (_id, *row) in enumerate(cursor):
                    if _id != id:
                        raise ValueError('"%s" column must by an incremental id')

                    if args.mode == 'json':
                        yield (json.dumps(zip(columns, row))).encode()
                    elif args.mode == 'raw':
                        yield b''.join(row)

        except Exception as ex:
            self.logger.error(ex)

    def query_callback(self, req, resp):
        self.logger.info(req, resp)


if __name__ == '__main__':
    parser = set_client_cli_parser()
    parser.add_argument('--limit', type=int, help='number of postgres rows (-1 for unlimited)')
    cred_repo_help = 'cred repo set up according to git:koursaros-ai/koursaros.credentials spec'
    parser.add_argument('--git_dsn', type=str, required=True, help=cred_repo_help)
    parser.add_argument('--yaml_path', type=str)
    cli_args = parser.parse_args()
    yaml = TrainableBase.load_yaml(cli_args.yaml_path)
    for k, v in yaml['parameters'].items(): setattr(cli_args, k, v)
    PostgresClient(cli_args)
