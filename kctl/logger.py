
from pygments.formatters import get_formatter_by_name
from logutils.colorize import ColorizingStreamHandler
import pygments.lexers
import traceback
import inspect
import logging
import sys

BOLD_BLACK = '\033[1m'
BOLD_GREEN = '\033[1;32m'
BOLD_YELLOW = '\033[1;33m'
BOLD_RED = '\033[1;31m'
RED_BACKGROUND = '\033[1;5;97;41m'
ITALICIZED = '\033[3m'
RESET = '\033[0m'

LEVEL_MAP = {
    0: RESET,
    10: BOLD_BLACK,
    20: BOLD_GREEN,
    30: BOLD_YELLOW,
    40: BOLD_RED,
    50: RED_BACKGROUND,
}


class KctlHandler(ColorizingStreamHandler):
    

    def colorize(self, record):
        """
        Get a special format string with ASCII color codes.
        """

        # Dynamic message color based on logging level
        levelno = round(record.levelno, -1)
        color_code = LEVEL_MAP[levelno]

        print(f"\033]0;{record.name}\007", end = '')
        print(f"\033]1;{record.module}\007", end = '')
        format_part_1 = f"%(asctime)s {BOLD_BLACK}[%(name)s.%(module)s] {color_code}%(levelname)s:"
        format_part_2 = f"{RESET} %(funcName)s(): %(message)s"
        format = format_part_1 + format_part_2
        # record.process =  f'{funcn}():{lineno}'

        formatter = logging.Formatter(format, "%H:%m:%S")
        self.colorize_traceback(formatter, record)
        output = formatter.format(record)
        # Clean cache so the color codes of traceback don't leak to other formatters
        record.ext_text = None
        return output


    def colorize_traceback(self, formatter, record):
        if record.exc_info:
            tb_type, value, tb = record.exc_info
            tb_text = "".join(traceback.format_exception(tb_type, value, tb))
            lexer = pygments.lexers.get_lexer_by_name("pytb", stripall=True)
            formatter = get_formatter_by_name('terminal')
            tb_colored = pygments.highlight(tb_text, lexer, formatter)
            record.exc_text = tb_colored


    def format(self, record):
        if self.is_tty:
            message = self.colorize(record)
        else:
            message = logging.StreamHandler.format(self, record)
        return message


def unhandled_exception(type, value, tb):
    logger = logging.getLogger("kctl")
    logger.exception('',exc_info=(type, value, tb))


def set_kctl_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = KctlHandler(sys.stdout)
    logger.addHandler(handler)
    sys.excepthook = unhandled_exception