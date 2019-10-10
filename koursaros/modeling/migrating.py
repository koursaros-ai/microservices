import transformers
from fairseq.data.data_utils import collate_tokens
import time
import torch.nn.functional as F
import torch.hub
import torch.jit

MAX_LENGTH = 512
PAD = True

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def benchmark_mnli(samples):
    torch_hub_model = time_fn(torch.hub.load, 'pytorch/fairseq','roberta.large.mnli')
    torch_hub_model.eval()
    torch_hub_model.cuda()
    try:
        transformers_model = time_fn(transformers.RobertaModel.from_pretrained,
                                     'roberta-large-mnli')
    except:
        transformers_model = time_fn(transformers.RobertaModel.from_pretrained,
                                     'roberta-large-mnli', force_download=True)
    transformers_model = transformers_model.to(device)
    transformers_tokenizer = time_fn(transformers.RobertaTokenizer.from_pretrained, 'roberta-large-mnli')
    transformers_traced = torch.jit.trace(transformers_model, get_dummy_data(transformers_tokenizer))
    pred_functions = {
        'transformers' : predict_transformers(transformers_model, transformers_tokenizer),
        'transformers-traced': predict_transformers(transformers_traced, transformers_tokenizer),
        'torch_hub' : predict_roberta(torch_hub_model)
    }
    for framework, pred_fn in pred_functions.items():
        print(f'Benchmarking {framework} with {samples} samples')
        time_fn(benchmark, pred_fn, samples)

def get_dummy_data(tokenizer):
    args = ['All work and no play make jack.'] * 8, ['Make jack a very dull boy.'] * 8
    inputs = transformers_encode_batch(tokenizer, *args)
    return torch.tensor(inputs[0], dtype=torch.long).to(device), \
           torch.tensor(inputs[1], dtype=torch.long).to(device)


def predict_transformers(model, tokenizer):
    def predict_fn(*args):
        inputs = time_fn(transformers_encode_batch, tokenizer, *args)
        inputs_dict = {
            'input_ids': torch.tensor(inputs[0],  dtype=torch.long).to(device),
            'attention_mask': torch.tensor(inputs[1],  dtype=torch.long).to(device),
        }
        outputs = model(inputs_dict['input_ids'], inputs_dict['attention_mask'])
        logits = outputs[0]
        preds = F.log_softmax(logits, dim=-1)
        return preds.tolist()
    return predict_fn


def predict_roberta(model):
    def pred_fn(*args):
        batch = time_fn(collate_tokens, [model.encode(*arg)[:MAX_LENGTH] for arg in zip(*args)], pad_idx=1)
        labels = model.predict('mnli', batch).tolist()
        return labels
    return pred_fn


def benchmark(pred_fn, n):
    args = ['The group turned to the recording proper on 1 May 1969.'] * 8, \
           ['''Writing for the TV play progressed through May and June, and on 15 June mixing for Dave Davies' solo LP was completed (tapes for this record were eventually delivered to Pye and Reprise Records, although it never saw official release).'''] * 8
    for i in range(0, n):
        assert(type(pred_fn(*args)) == list)

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
    input_ids = inputs["input_ids"][:MAX_LENGTH]

    return input_ids

def pad_up(input_ids, max_length):
    padding_length = max_length - len(input_ids)
    input_ids = ([0] * padding_length) + input_ids
    attention_mask = ([0] * padding_length) + [1] * len(input_ids)
    return (input_ids, attention_mask)


def transformers_encode_batch(tokenizer, *args):
    assert(type(args[0]) == list)
    all_input_ids = []
    max_batch_len = 0

    for sample in zip(*args):
        input_ids = transformer_to_features(tokenizer, *sample)
        all_input_ids.append(input_ids)
        max_batch_len = max(max_batch_len, len(input_ids))

    all_input_ids, all_attention_masks = zip(*[
        pad_up(input_ids, MAX_LENGTH) for input_ids in all_input_ids
    ])
    return all_input_ids, all_attention_masks


if __name__ == '__main__':
    with torch.no_grad():
        benchmark_mnli(10)