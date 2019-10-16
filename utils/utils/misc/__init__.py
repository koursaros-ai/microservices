
import os

BOLD = '\033[1m{}\033[0m'


def gb_free_space():
    statvfs = os.statvfs(os.getcwd())
    return statvfs.f_frsize * statvfs.f_bfree / 1e+9      # Actual number of free bytes


def batch_fn(batch_size, call_fn, items):
    buffer = []
    for item in items:
        buffer.append(item)
        if len(buffer) % batch_size == 0:
            yield call_fn(buffer), buffer
            buffer = []
    if len(buffer) > 0:
        yield call_fn(buffer), buffer


def batch_list(arr, n):
    buffer = []
    for i, item in enumerate(arr):
        buffer.append(item)
        if (i+1) % n == 0:
            yield buffer
            buffer = []
    if len(buffer) > 0:
        yield buffer
