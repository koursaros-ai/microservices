
import time
import sys
from .utils import find_app_path
import os

APP_PATH = find_app_path(os.getcwd())

BOLD = '\033[1m'
GREEN = '\033[32m'
RED = '\033[1;31m'

BOLD_YELLOW = '\033[1;33m'
RED_BACKGROUND = '\033[1;5;97;41m'
ITALICIZED = '\033[3m'
RESET = '\033[0m'


class Stdout:
    stdout = None
    name = None
    outfile = open(APP_PATH + '/.koursaros/kctl-stdout.log', 'w') if APP_PATH else None

    @staticmethod
    def __init__(stdout, name):
        Stdout.stdout = stdout
        Stdout.name = name

    @staticmethod
    def fileno():
        return 1

    @staticmethod
    def write(record=''):
        if record != '\n':
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            code = sys._getframe(1).f_code
            name = code.co_name
            file = code.co_filename[-30:]
            dots = '...' if len(file) == 30 else ''

            log = (
                f'{timestamp} [{BOLD}{Stdout.name}] {GREEN}STDOUT:'
                f'{RESET} {dots}{file} → ️{name}(): {record}\n'
            )

            Stdout.stdout.write(log)
            if Stdout.outfile:
                Stdout.outfile.write(log)


    @staticmethod
    def flush():
        pass


class Stderr:
    stderr = None
    name = None
    errfile = open(APP_PATH + '/.koursaros/kctl-stderr.log', 'w') if APP_PATH else None

    @staticmethod
    def __init__(stderr, name):
        Stderr.stderr = stderr
        Stderr.name = name

    @staticmethod
    def fileno():
        return 2

    @staticmethod
    def write(record=''):
        if record != '\n':
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log = f'{timestamp} [{BOLD}{Stderr.name}] {RED}STDERR:{RESET} {record.rstrip()}\n'

            Stderr.stderr.write(log)

            if Stderr.errfile:
                Stderr.errfile.write(log)

    @staticmethod
    def flush():
        pass


def redirect_out(name):
    sys.stdout = Stdout(sys.stdout, name)
    sys.stderr = Stderr(sys.stderr, name)


