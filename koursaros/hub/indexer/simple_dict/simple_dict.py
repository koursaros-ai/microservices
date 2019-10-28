from typing import List

from google.protobuf.json_format import MessageToJson, Parse

from gnes.indexer.base import BaseDocIndexer as BDI
from gnes.proto import gnes_pb2


class SimpleDictIndexer(BDI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = {}

    @BDI.update_counter
    def add(self, keys: List[int], docs: List['gnes_pb2.Document'], *args, **kwargs):
        self.logger.error(keys)
        self.logger.error(docs)
        self._content.update({k: MessageToJson(d) for (k, d) in zip(keys, docs)})

    def query(self, keys: List[int], *args, **kwargs) -> List['gnes_pb2.Document']:
        self.logger.error(keys)
        return [Parse(self._content[k], gnes_pb2.Document()) for k in keys]