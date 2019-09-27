def batch_fn(batch_size, call_fn, items):
    buffer = []
    for item in items:
        buffer.append(item)
        if len(buffer) % batch_size == 0:
            yield call_fn(buffer), buffer
            buffer = []
    if len(buffer) > 0:
        yield call_fn(buffer), buffer
