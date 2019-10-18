from typing import List

import numpy as np

from gnes.encoder.base import BaseTextEncoder
from gnes.helper import batching, as_numpy_array


class TextIntEncoder(BaseTextEncoder):
    """Returns np array of encoded text. Useful for text search."""
    is_trained = True

    @batching
    @as_numpy_array
    def encode(self, text: List[str], *args, **kwargs) -> List:
        arrays = [int.from_bytes(sent.encode(), byteorder="big") for sent in text]
        self.logger.error(arrays)
        return arrays
