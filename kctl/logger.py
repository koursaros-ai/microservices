
from time import strftime
from sys import stdout, stderr, _getframe


BOLD = '\033[1m'
GREEN = '\033[32m'
RED = '\033[1;31m'

BOLD_YELLOW = '\033[1;33m'
RED_BACKGROUND = '\033[1;5;97;41m'
ITALICIZED = '\033[3m'
RESET = '\033[0m'


class KctlLogger:
    name = 'kctl'
    stdout_write = stdout.write
    stderr_write = stderr.write
    stdout_label = ''
    stderr_label = ''

    @classmethod
    def init(cls, name='kctl'):
        cls.name = name
        cls.stdout_label = f'[{BOLD}{cls.name}] {GREEN}STDOUT:{RESET}'
        cls.stderr_label = f'[{BOLD}{cls.name}] {RED}STDERR:{RESET}'
        stdout.write = cls.stdout_wrap
        stderr.write = cls.stderr_wrap
        print('\tWrapping stdout with KctlLogger...')

    @staticmethod
    def timestamp():
        return strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def stack():
        code = _getframe(2).f_code
        name = code.co_name
        file = code.co_filename[-50:]
        dots = '...' if len(file) == 50 else ''
        return dots, file, name
        # return f'{dots}{file} → ️{name}(): '

    @staticmethod
    def stdout_wrap(record=''):
        KctlLogger.format_line(record)

    @staticmethod
    def stderr_wrap(record=''):
        KctlLogger.format_line(record, err=True)

    @classmethod
    def format_line(cls, record, err=False):
        label = cls.stderr_label if err else cls.stdout_label
        write = cls.stderr_write if err else cls.stdout_write

        if record == '\n':
            dots, file, name = cls.stack()
            # write(record + cls.timestamp() + label + cls.stack() + '\n\t')
            write(record + cls.timestamp() + label + '\n\t')
        else:
            # write(record.replace('\n', '\n\t'))
            write(record)
