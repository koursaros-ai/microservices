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
        self.size = 0

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, _, *args, **kwargs):
        if vectors.dtype != np.uint8:
            raise ValueError('vectors should be ndarray of uint8')

        for key, vector in zip(keys, vectors):
            self._automaton.add_word(self.decode_textbytes(vector), key)
            self.size += 1

        self.logger.error(list(self._automaton.keys()))

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        if keys.dtype != np.uint8:
            raise ValueError('vectors should be ndarray of uint8')
        elif not self.size > 0:
            print('Warning: empty index queried')
            return []

        self._automaton.make_automaton()

        ret = []
        for key in keys:
            ret_i = defaultdict(int)
            for _, (doc_id, offset) in self._automaton.iter(self.decode_textbytes(key)):
                ret_i[(doc_id, offset)] += 1

            # _doc_id, _offset, _weight, _relevance
            results = [(*k, 1.0, v) for k, v in ret_i.items()]
            # topk by number of keyword matches
            ret.append(sorted(results, reverse=True, key=lambda x: x[-1])[:top_k])

        return ret

    @staticmethod
    def decode_textbytes(vector: np.ndarray):
        return vector.tobytes().rstrip(b'\x00').decode()
