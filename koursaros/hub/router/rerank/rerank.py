from typing import List

from gnes.router.base import BaseReduceRouter
from gnes.proto import gnes_pb2
from transformers import *

class RerankRouter(BaseReduceRouter):

    def __init__(self, model_name: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name

    def post_init(self):
        self.rerank_model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def get_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult') -> str:
        raise NotImplementedError

    def set_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult', k: str) -> None:
        raise NotImplementedError

    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):
        # now convert chunk results to doc results
        all_scored_results = [sr for m in accum_msgs for sr in m.response.search.topk_results]
        print(all_scored_results)
        # score_dict = dict() # ?
        #
        # # count score by iterating over chunks
        # for c in all_scored_results:
        #     score_dict[self.get_key(c)].append(c.score)
        #
        # for k, v in score_dict.items():
        #     score_dict[k] = self.reduce_op(*v)
        #
        msg.response.search.ClearField('topk_results')
        #
        # for k, v in score_dict.items():
        #     r = msg.response.search.topk_results.add()
        #     r.score.CopyFrom(v)
        #     self.set_key(r, k)

        super().apply(msg, accum_msgs)