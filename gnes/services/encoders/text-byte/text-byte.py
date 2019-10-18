from typing import List

import numpy as np

from gnes.encoder.base import BaseTextEncoder
from gnes.helper import batching, as_numpy_array


class TextByteEncoder(BaseTextEncoder):
    """Returns np array of encoded text. Useful for text search."""
    is_trained = True

    @batching
    @as_numpy_array
    def encode(self, text: List[str], *args, **kwargs) -> List[np.ndarray]:
        return [np.array([ord(c) for c in sent]) for sent in text]
