
import logging
from logging import Formatter
from termcolor import colored
from copy import copy
import os

BOLD_LEVELNO = 25


def bold(self, message, *args, **kws):
    if self.isEnabledFor(BOLD_LEVELNO):
        self._log(BOLD_LEVELNO, message, args, **kws)


logging.Logger.debugv = bold


class ColoredFormatter(Formatter):
    MAPPING = {
        'DEBUG': dict(color='magenta', on_color=None),
        'INFO': dict(color='blue', on_color=None),
        'BOLD': dict(color='cyan', on_color=None),
        'WARNING': dict(color='yellow', on_color=None),
        'ERROR': dict(color='red', on_color=None),
        'CRITICAL': dict(color='white', on_color='on_red'),
    }

    PREFIX = '\033['
    SUFFIX = '\033[0m'

    def format(self, record):
        cr = copy(record)
        seq = self.MAPPING.get(cr.levelname, self.MAPPING['INFO'])  # default info
        cr.msg = colored(cr.msg, **seq)
        return super().format(cr)


def set_logger(context, verbose=False):
    if os.name == 'nt':  # for Windows
        return NTLogger(context, verbose)

    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.addLevelName(BOLD_LEVELNO, "BOLD")
    logger = logging.getLogger(context)
    logger.propagate = False
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = ColoredFormatter(
            '%(levelname)-.3s:\033[1m[' + context +
            '.%(module)s]\033[0m:%(funcName)-.5s:'
            '%(lineno)s: %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        console_handler.setFormatter(formatter)
        logger.handlers = []
        logger.addHandler(console_handler)

    return logger


class NTLogger:
    def __init__(self, context, verbose):
        self.context = context
        self.verbose = verbose

    def info(self, msg, **kwargs):
        print('I:%s:%s' % (self.context, msg), flush=True)

    def debug(self, msg, **kwargs):
        if self.verbose:
            print('D:%s:%s' % (self.context, msg), flush=True)

    def error(self, msg, **kwargs):
        print('E:%s:%s' % (self.context, msg), flush=True)

    def warning(self, msg, **kwargs):
        print('W:%s:%s' % (self.context, msg), flush=True)
