from typing import List
from collections import defaultdict, OrderedDict
import json

from gnes.router.base import BaseReduceRouter
from gnes.proto import gnes_pb2
from gnes.helper import batching

from transformers import *
import torch
import torch.nn
import numpy as np


class RerankRouter(BaseReduceRouter):

    def __init__(self, model_name: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.max_grad_norm = 1.0
        self.lr = 1e-3

    def post_init(self):
        model_config = AutoConfig.from_pretrained(self.model_name)
        model_config.num_labels = 1 # set up for regression
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.rerank_model = AutoModelForSequenceClassification.from_pretrained(self.model_name,
                                                                               config=model_config)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.rerank_model.to(self.device)

        self.optimizer = AdamW(self.rerank_model.parameters(), lr=self.lr, correct_bias=False)
        self.scheduler = ConstantLRSchedule(self.optimizer)

    def get_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult') -> str:
        return x.doc.doc_id

    def set_key(self, x: 'gnes_pb2.Response.QueryResponse.ScoredResult', k: str) -> None:
        x.doc.doc_id = k

    @batching
    def apply(self, msg: 'gnes_pb2.Message', accum_msgs: List['gnes_pb2.Message'], *args, **kwargs):

        all_scored_results = [sr for m in accum_msgs for sr in m.response.search.topk_results]
        score_dict = defaultdict(list)

        if len(msg.request.train.docs) > 0:  # training samples are given
            inputs = [
                self.tokenizer.encode_plus(
                    json.loads(doc.raw_text)['query'],
                    json.loads(doc.raw_text)['cand'],
                    add_special_tokens=True
                ) for doc in msg.request.train.docs
            ]
            labels = torch.tensor([json.loads(doc.raw_text)['label'] for doc in msg.request.train.docs],
                                  dtype=torch.float).to(self.device)
        elif len(all_scored_results) > 0:
            inputs = [
                self.tokenizer.encode_plus(
                    msg.request.search.query.raw_text,
                    sr.doc.raw_text,
                    add_special_tokens=True,
                ) for sr in all_scored_results]
            labels = None
            
        else:
            return

        if len(inputs) == 0:
            print("Warning: empty input set, ignoring.")
            super().apply(msg, accum_msgs)
            return

        max_len = max(len(t['input_ids']) for t in inputs)
        input_ids = [t['input_ids'] + [0] * (max_len - len(t['input_ids'])) for t in inputs]
        token_type_ids = [t['token_type_ids'] + [0] * (max_len - len(t['token_type_ids'])) for t in inputs]
        attention_mask = [[1]*len(t['input_ids']) + [0] * (max_len - len(t['input_ids'])) for t in inputs]

        input_ids = torch.tensor(input_ids).to(self.device)
        token_type_ids = torch.tensor(token_type_ids).to(self.device)
        attention_mask = torch.tensor(attention_mask).to(self.device)

        if labels is not None:
            loss = self.rerank_model(input_ids, token_type_ids=token_type_ids,
                                        labels=labels, attention_mask=attention_mask)[0]
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.rerank_model.parameters(), self.max_grad_norm)
            self.optimizer.step()
            self.scheduler.step()
            self.rerank_model.zero_grad()
            msg.response.train.status = gnes_pb2.Response.Status.SUCCESS

        else:
            with torch.no_grad():
                logits = self.rerank_model(input_ids, token_type_ids=token_type_ids,
                                           attention_mask=attention_mask)[0]
                scores = np.squeeze(logits.detach().cpu().numpy())

            for c, score in zip(all_scored_results, scores):
                score_dict[self.get_key(c)].append(score)

            for k, v in score_dict.items():
                score_dict[k] = sum(v)

            k = msg.response.search.top_k
            score_dict = OrderedDict(sorted(score_dict.items(), key=lambda x: x[1], reverse=True)[:k])

            msg.response.search.ClearField('topk_results')
            for k, v in score_dict.items():
                r = msg.response.search.topk_results.add()
                r.score.value = float(v)
                self.set_key(r, k)

        super().apply(msg, accum_msgs)