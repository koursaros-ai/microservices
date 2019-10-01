
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
        print('Wrapping stdout with KctlLogger...')

    @staticmethod
    def timestamp():
        return strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def stack():
        code = _getframe(1).f_code
        name = code.co_name
        file = code.co_filename[-20:]
        dots = '...' if len(file) == 20 else ''
        return name, file, dots

    @staticmethod
    def stdout_wrap(record=''):
        if record == '\n':
            timestamp = KctlLogger.timestamp()
            name, file, dots = KctlLogger.stack()
            call = f'{dots}{file} → ️{name}():'
            to_write = record + timestamp + KctlLogger.stdout_label + call
            KctlLogger.stdout_write(to_write)
        else:
            KctlLogger.stdout_write(record)

    @staticmethod
    def stderr_wrap(record=''):
        if record == '\n':
            timestamp = KctlLogger.timestamp()
            to_write = record + timestamp + KctlLogger.stderr_label
            KctlLogger.stderr_write(to_write)
        else:
            KctlLogger.stderr_write(record)

