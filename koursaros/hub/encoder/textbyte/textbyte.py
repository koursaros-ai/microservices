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

    def pad_and_vector(self, sent):
        padded = sent.encode()[:self._msl] + b'\x00' * (self._msl - len(sent.encode()))
        try:
            bytes(padded).decode()
            return np.frombuffer(padded, dtype=np.int8)
        except:  # split aup a multibyte character, so take off one more
            padded = padded[:-2] + b'\x00' * 2
            return self.pad_and_vector(padded.decode())

    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        encoded = np.stack([self.pad_and_vector(sent) for sent in text])
        return encoded

