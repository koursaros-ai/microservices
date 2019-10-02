
from time import strftime
from sys import stdout, stderr
from inspect import stack
import logging
logging.basicConfig(stream=stderr, level=logging.ERROR)


BOLD = '\033[1m'
GREEN = '\033[32m'
RED = '\033[1;31m'

BOLD_YELLOW = '\033[1;33m'
RED_BACKGROUND = '\033[1;5;97;41m'
ITALICIZED = '\033[3m'
RESET = '\033[0m'


class KctlLogger:
    stdout_write = stdout.write
    stderr_write = stderr.write
    newline = True

    @classmethod
    def init(cls):
        stdout.write = cls.stdout_wrap
        stderr.write = cls.stderr_wrap
        print('Wrapping stdout with KctlLogger...')

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
        write = cls.stderr_write if err else cls.stdout_write

        if err:
            label = f' {BOLD}{RED}STDERR:{RESET} '
        else:
            s2 = stack()[2]
            func = s2.function
            lineno = s2.lineno
            name = s2.frame.f_globals.get('__package__', '')
            label = f' {BOLD}[{name}.{func}({lineno})] {GREEN}STDOUT:{RESET} '

        line = cls.timestamp() + label

        if cls.newline:
            write(line)
            cls.newline = False

        if record[-1] == '\n':
            cls.newline = True
            record = record[:-1]

        write(record.replace('\n', '\n' + line))

        if cls.newline:
            write('\n')



