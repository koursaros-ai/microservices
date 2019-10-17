from gnes.cli.parser import set_client_cli_parser
from koursaros.credentials import get_creds
from gnes.client.cli import CLIClient
from gnes.base import TrainableBase
import psycopg2
import os


class PostgresClient(CLIClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        a = self.args
        self.creds = get_creds(a.cred_repo,
                               username=a.cred_user,
                               password=a.cred_pass)

        p = self.creds.postgres
        self.configs = dict(user=p.username,
                            password=p.password,
                            host=p.host,
                            port=p.port,
                            dbname=p.dbname)

        os.environ['PGSSLMODE'] = p.pgsslmode
        os.environ['PGSSLROOTCERT'] = p.pgsslrootcert.path

        self.query = '''SELECT %s, %s, %s FROM %s''' % (a.col_one,
                                                        a.col_two,
                                                        a.col_label,
                                                        a.table)
        self.query += 'LIMIT %d' % a.limit if a.limit > 0 else ''

    @property
    def bytes_generator(self):
        connection = psycopg2.connect(**self.configs)
        cursor = connection.cursor()
        cursor.execute(self.query % self.args.limit)

        for i, (text_one, text_two, label) in enumerate(cursor):
            yield (text_one + text_two + str(label)).encode()

    def query_callback(self, req, resp):
        self.logger.info(req, resp)


if __name__ == '__main__':
    parser = set_client_cli_parser()
    parser.add_argument('--limit', type=int, help='number of postgres rows (-1 for unlimited)')
    cred_repo_help = 'cred repo set up according to git:koursaros-ai/koursaros.credentials spec'
    parser.add_argument('--cred_repo', type=str, required=True, help=cred_repo_help)
    parser.add_argument('--cred_user', type=str)
    parser.add_argument('--cred_pass', type=str)
    parser.add_argument('--yaml_path', type=str)
    args = parser.parse_args()
    yaml = TrainableBase.load_yaml(args.yaml_path)
    for k, v in yaml['parameters'].items(): setattr(args, k, v)
    PostgresClient(args)
