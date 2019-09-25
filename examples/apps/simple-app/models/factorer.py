from functools import reduce


class Factorer:
    def factor(self, n):
        return set(reduce(
            list.__add__,
            ([i, n // i] for i in range(1, int(n ** 0.5) + 1))
        ))