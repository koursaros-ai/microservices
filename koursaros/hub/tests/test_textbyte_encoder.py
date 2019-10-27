import unittest
from koursaros.hub.encoder.textbyte.textbyte import TextByteEncoder

class TestTextByte(unittest.TestCase):

    def setUp(self) -> None:
        self.msl = 64
        self.model = TextByteEncoder(self.msl)

    def test_textbyte(self):
        vectors = self.model.encode([
            "This is a really long sentence it's really long, I can't even tell you how long it is.",
            "This is a shorter sentence",
            "This"])
        for vec in vectors:
            self.assertEqual(len(vec), self.msl)