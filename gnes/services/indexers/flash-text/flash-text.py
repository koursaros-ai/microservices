
from typing import List, Tuple
import numpy as np

from gnes.indexer.base import BaseChunkIndexer as BCI


class FlashTextIndexer(BCI):

    def __init__(self, *args, **kwargs):
        """
        Initialize a Flash Text Indexer
        :param data_path: index data file
        """
        super().__init__(*args, **kwargs)
        self._flash_index = dict()

    def post_init(self):
        from flashtext import KeywordProcessor
        self._keyword_processor = KeywordProcessor()

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, _, *args, **kwargs):
        if np.issubdtype(vectors.dtype, np.integer):
            raise ValueError('vectors should be ndarray of np.integer')

        for key, vector in zip(keys, vectors):
            self._flash_index[key] = self.decode_ndarray(vector)

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        if np.issubdtype(keys.dtype, np.integer):
            raise ValueError('text queries should be ndarray of np.integer')

        ret = []
        for key in keys:
            self._keyword_processor.keyword_trie_dict.clear()
            self._keyword_processor.add_keyword(self.decode_ndarray(key))
            ret_i = dict()
            for (doc_id, offset), text in self._flash_index.items():
                matches = len(self._keyword_processor.extract_keywords(text))
                if matches: ret_i[doc_id] = matches

            # topk by number of keyword matches
            ret.append(sorted(enumerate(ret_i), reverse=True, key=lambda x: x[1])[:top_k])

        return ret

    @staticmethod
    def decode_ndarray(array):
        return bytes(array.tolist()).decode()