import sys
import transformers
from fairseq.models import roberta
from fairseq.data.data_utils import collate_tokens
import time
import torch.nn.functional as F
import torch.hub

# def roberta_to_transformer(path_to_roberta, path_to_yaml):
#     model = RobertaModel.from_pretrained(path_to_roberta, checkpoint_file='model.pt')
#     model.eval()

MAX_LENGTH = 256
PAD = True

def predict_transformers(model, tokenizer):
    def predict_fn(*args):
        inputs = time_fn(transformers_encode_batch, tokenizer, *args)
        inputs_dict = {
            'input_ids': torch.tensor(inputs[0],  dtype=torch.long),
            'attention_mask': torch.tensor(inputs[1],  dtype=torch.long),
            'token_type_ids': torch.tensor(inputs[2],  dtype=torch.long)
        }
        import pdb
        pdb.set_trace()
        outputs = model(**inputs_dict)
        logits = outputs[0]
        preds = F.log_softmax(logits, dim=-1)
        return preds.tolist()
    return predict_fn


def predict_roberta(model):
    def pred_fn(*args):
        batch = time_fn(collate_tokens, [model.encode(*arg)[:MAX_LENGTH] for arg in zip(*args)], pad_idx=1)
        labels = model.predict('mnli', *batch).tolist()
        return labels
    return pred_fn


def benchmark(pred_fn, n):
    args = ['All work and no play.'] * 8, ['Make jack a very dull boy.'] * 8
    for i in range(0, n):
        assert(type(pred_fn(*args)) == list)


def benchmark_mnli(samples):
    torch_hub_model = time_fn(torch.hub.load, 'pytorch/fairseq','roberta.large.mnli')
    try:
        transformers_model = time_fn(transformers.RobertaModel.from_pretrained,
                                     'roberta-large-mnli')
    except:
        transformers_model = time_fn(transformers.RobertaModel.from_pretrained,
                                     'roberta-large-mnli', force_download=True)
    transformers_tokenizer = time_fn(transformers.RobertaTokenizer.from_pretrained, 'roberta-large-mnli')
    pred_functions = {
        'transformers' : predict_transformers(transformers_model, transformers_tokenizer),
        'torch_hub' : predict_roberta(torch_hub_model)
    }
    for framework, pred_fn in pred_functions.items():
        print(f'Benchmarking {framework} with {samples} samples')
        time_fn(benchmark, pred_fn, samples)

### HELPERS

def time_fn(fn, *args, **kwargs):
    start = time.time()
    res = fn(*args, **kwargs)
    print(f'Took {time.time() - start} seconds to run {fn.__name__}')
    return res


def transformer_to_features(tokenizer, *args):
    inputs = tokenizer.encode_plus(
        *args,
        add_special_tokens=True,
        max_length=MAX_LENGTH,
        truncate_first_sequence=True
    )
    input_ids, token_type_ids = inputs["input_ids"][:MAX_LENGTH], \
                                inputs["token_type_ids"][:MAX_LENGTH]

    attention_mask = [1] * len(input_ids)

    # Zero-pad up to the sequence length.
    if PAD:
        padding_length = MAX_LENGTH - len(input_ids)
        input_ids = ([0] * padding_length) + input_ids
        attention_mask = ([0] * padding_length) + attention_mask
        token_type_ids = ([0] * padding_length) + token_type_ids

    return (input_ids, attention_mask, token_type_ids)


def transformers_encode_batch(tokenizer, *args):
    assert(type(args[0]) == list)
    all_input_ids = []
    all_attention_mask = []
    all_token_type_ids = []
    for sample in zip(*args):
        input_ids, attention_mask, token_type_ids = transformer_to_features(tokenizer, *sample)
        all_input_ids.append(input_ids)
        all_attention_mask.append(attention_mask)
        all_token_type_ids.append(token_type_ids)
    return all_input_ids, all_attention_mask, all_token_type_ids


if __name__ == '__main__':
    benchmark_mnli(10)