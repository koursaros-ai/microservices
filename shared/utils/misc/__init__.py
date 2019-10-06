import os

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
