
from typing import List, Tuple
import numpy as np
from collections import defaultdict

from gnes.indexer.base import BaseChunkIndexer as BCI


class KeywordIndexer(BCI):

    def __init__(self, *args, **kwargs):
        """
        Initialize an indexer that implements the AhoCorasick Algorithm
        """
        super().__init__(*args, **kwargs)
        import ahocorasick
        self._automaton = ahocorasick.Automaton()

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, _, *args, **kwargs):
        if vectors.dtype != np.uint8:
            raise ValueError('vectors should be ndarray of uint8')

        for key, vector in zip(keys, vectors):
            self._automaton.add_word(self.decode_textbytes(vector), key)

        self.logger.error(list(self._automaton.keys()))

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        if keys.dtype != np.uint8:
            raise ValueError('vectors should be ndarray of uint8')

        self._automaton.make_automaton()

        ret = []
        for key in keys:
            ret_i = defaultdict(lambda: 0)
            for _, (doc_id, _) in self._automaton.iter(self.decode_textbytes(key)):
                ret_i[doc_id] += 1

            # topk by number of keyword matches
            ret.append(sorted(enumerate(ret_i), reverse=True, key=lambda x: x[1])[:top_k])

        return ret

    @staticmethod
    def decode_textbytes(vector: np.ndarray):
        return vector.tobytes().rstrip(b'\x00').decode()
