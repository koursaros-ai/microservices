from typing import List

import numpy as np

from gnes.encoder.base import BaseTextEncoder
from gnes.helper import batching


class TextByteEncoder(BaseTextEncoder):
    """Returns np array of encoded text. Useful for text search."""
    is_trained = True

    @batching
    def encode(self, text: List[str], *args, **kwargs) -> np.ndarray:
        array = np.array([np.ndarray([int.from_bytes(sent.encode(), byteorder="big")]) for sent in text])
        self.logger.error(array)
        return array
