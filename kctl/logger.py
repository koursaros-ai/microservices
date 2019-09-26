
import time
import sys

BOLD = '\033[1m'
GREEN = '\033[32m'
RED = '\033[1;31m'

BOLD_YELLOW = '\033[1;33m'
RED_BACKGROUND = '\033[1;5;97;41m'
ITALICIZED = '\033[3m'
RESET = '\033[0m'


class KctlStdout:
    stdout = None
    outfile = open('kctl-stdout.log', 'w')

    @staticmethod
    def __init__(stdout):
        KctlStdout.stdout = stdout

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
                f'{timestamp} [{BOLD}kctl] {GREEN}STDOUT:'
                f'{RESET} {dots}{file} → ️{name}(): {record}\n'
            )

            KctlStdout.stdout.write(log)
            KctlStdout.outfile.write(log)


    @staticmethod
    def flush():
        pass


class KctlStderr:
    stderr = None
    errfile = open('kctl-stderr.log', 'w')

    @staticmethod
    def __init__(stderr):
        KctlStderr.stderr = stderr

    @staticmethod
    def fileno():
        return 2

    @staticmethod
    def write(record=''):
        # if record != '\n':
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log = f'{timestamp} [{BOLD}kctl] {RED}STDERR:{RESET} {record.rstrip()}\n'

        KctlStderr.stderr.write(log)
        KctlStderr.errfile.write(log)

    @staticmethod
    def flush():
        pass


def redirect_out():
    sys.stdout = KctlStdout(sys.stdout)
    sys.stderr = KctlStderr(sys.stderr)


