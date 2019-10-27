import unittest
from koursaros.hub.encoder.textbyte.textbyte import TextByteEncoder

class TestTextByte(unittest.TestCase):

    def setUp(self) -> None:
        self.model = TextByteEncoder(64)

    def test_textbyte(self):
        vectors = self.model.encode([
            "This is a really long sentence it's really long ",
            "This is a shorter sentence",
            "This"])
        for vec in vectors:
            print(len(vec))