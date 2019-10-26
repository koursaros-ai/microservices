from typing import List, Tuple
import numpy as np
import os, os.path
from whoosh import index, scoring
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh.analysis import StemmingAnalyzer
from whoosh.qparser import QueryParser
from whoosh.writing import SegmentWriter
from whoosh.codec import default_codec
from whoosh.automata import lev
from whoosh.searching import Searcher
from whoosh import collectors

from gnes.indexer.base import BaseChunkIndexer as BCI


class WhooshIndexer(BCI):

    def __init__(self, *args, **kwargs):
        """
        Initialize an indexer that implements the AhoCorasick Algorithm
        """
        super().__init__(*args, **kwargs)
        if not os.path.exists("indexdir"):
            os.mkdir("indexdir")

        schema = Schema(doc_id=NUMERIC(stored=True),
                        offset=NUMERIC(stored=True),
                        body=TEXT(analyzer=StemmingAnalyzer()))

        self.ix = index.create_in("indexdir", schema)

    def add(self, keys: List[Tuple[int, int]], vectors: np.ndarray, _, *args, **kwargs):
        if vectors.dtype != np.uint8:
            raise ValueError('vectors should be ndarray of uint8')

        writer = self.ix.writer()
        for key, vector in zip(keys, vectors):
            body = self.decode_textbytes(vector)
            writer.add_document(doc_id=key[0],offset=key[1],body=body)

        writer.commit()

    def query(self, keys: np.ndarray, top_k: int, *args, **kwargs) -> List[List[Tuple]]:
        if keys.dtype != np.uint8:
            raise ValueError('vectors should be ndarray of uint8')

        ret = []
        qp = QueryParser("body", schema=self.ix.schema)
        with self.ix.searcher(weighting=scoring.TF_IDF()) as searcher:
            for key in keys:
                query = qp.parse(self.decode_textbytes(key))
                ret.append([
                    (result['doc_id'],result['offset'], 1.0, 1.0)
                    for result in searcher.search(query, limit=top_k)])
        print(ret)
        return ret

    @staticmethod
    def decode_textbytes(vector: np.ndarray):
        return vector.tobytes().rstrip(b'\x00').decode()
