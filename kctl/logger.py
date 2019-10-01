
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
    def stdout_wrap(record=''):
        KctlLogger.format_line(record)

    @staticmethod
    def stderr_wrap(record=''):
        KctlLogger.format_line(record, err=True)

    @classmethod
    def format_line(cls, record, err=False):
        label = cls.stderr_label if err else cls.stdout_label
        write = cls. if err else cls.stdout_write

        if not err:
            code = _getframe(2).f_code
            name = code.co_name
            file = code.co_filename[-50:]
            dots = '...' if len(file) == 50 else ''
            # return dots, file, name
            stack = f'{dots}{file} → ️{name}(): '
            if record == '\n':
                cls.stdout_write(record + cls.timestamp() + label + stack + '\n\n\t')
            else:
                cls.stdout_write(record.replace('\n', '\n\t'))
        else:
            line = cls.timestamp() + label

            if record == '\n':
                cls.stderr_write(record + line)
            else:
                cls.stderr_write(record.replace('\n', '\n' + line))



