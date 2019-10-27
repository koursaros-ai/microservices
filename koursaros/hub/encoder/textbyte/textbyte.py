from typing import List

import numpy as np

from gnes.encoder.base import BaseTextEncoder
from gnes.helper import batching


class TextByteEncoder(BaseTextEncoder):
    """Returns np array of encoded text. Useful for text search."""
    is_trained = True

    def __init__(self, max_seq_len, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._msl = max_seq_len

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        encoded = np.array([np.frombuffer(
                sent.encode()[:self._msl] + b'\x00' * (self._msl - len(sent)),
                dtype=np.uint8
        ) for sent in text])
        self.logger.error(encoded.shape)
        return encoded

