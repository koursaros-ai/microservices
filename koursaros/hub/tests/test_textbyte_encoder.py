import unittest
from koursaros.hub.encoder.textbyte.textbyte import TextByteEncoder
import pathlib
import csv

class TestTextByte(unittest.TestCase):

    def setUp(self) -> None:
        self.msl = 1024
        self.model = TextByteEncoder(self.msl)
        self.path = pathlib.Path('reviews_sample.csv')
        self.csv = csv.DictReader(self.path.open())

    def test_textbyte(self):
        to_encode = []
        for row in self.csv:
            to_encode.append(list(row.values())[1])
        vectors = self.model.encode(to_encode)
        for vec in vectors:
            self.assertEqual(len(vec), self.msl)