from ..model import Model
import torch.nn, torch.tensor, torch.distributed
from transformers import *
from torch.utils.data import (DataLoader, RandomSampler, SequentialSampler,
                              TensorDataset)
from tqdm import tqdm, trange

MODEL_CLASSES = {
    'bert': (BertConfig, BertForSequenceClassification, BertTokenizer),
    'xlnet': (XLNetConfig, XLNetForSequenceClassification, XLNetTokenizer),
    'xlm': (XLMConfig, XLMForSequenceClassification, XLMTokenizer),
    'roberta': (RobertaConfig, RobertaForSequenceClassification, RobertaTokenizer),
    'distilbert': (DistilBertConfig, DistilBertForSequenceClassification, DistilBertTokenizer)
}


class TransformerModel(Model):

    def __init__(self, *args):
        super().__init__(*args)
        if self.config.task == 'classification':
            config, model, tokenizer = MODEL_CLASSES[self.config.base]
        else:
            raise NotImplementedError()

        self.model = model.from_pretrained(self.checkpoint)
        self.tokenizer = tokenizer.from_pretrained(self.checkpoint)

    def extract_features(self, data):
        return [self.tokenizer.encode(*b[:2], add_special_tokens=True) for b in data]

    def train(self):
        ### In Transformers, optimizer and schedules are splitted and instantiated like this:

        batch_size = 4
        max_grad_norm = 1.0
        weight_decay = 0.0
        n_gpu = 1
        local_rank = -1
        fp16 = False

        train_dataset, test_dataset = self.get_data()
        epochs = int(self.config.train.epochs)
        optimizer = AdamW(self.model.parameters(), lr=float(self.config.training.learning_rate),
                          correct_bias=False)  # To reproduce BertAdam specific behavior set correct_bias=False
        num_warmup_steps = int(0.06 * len(train_dataset))
        scheduler = WarmupLinearSchedule(optimizer, warmup_steps=num_warmup_steps,
                                         t_total=(self.config.training.epochs * len(train_dataset) / batch_size))
        self.model.train()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(device)

        train_sampler = RandomSampler(train_dataset)
        train_dataloader = DataLoader(train_dataset, sampler=train_sampler, batch_size=batch_size)

        t_total = len(train_dataloader) // epochs

        # Prepare optimizer and schedule (linear warmup and decay)
        no_decay = ['bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {'params': [p for n, p in self.model.named_parameters() if not any(nd in n for nd in no_decay)],
             'weight_decay': weight_decay},
            {'params': [p for n, p in self.model.named_parameters() if any(nd in n for nd in no_decay)],
             'weight_decay': 0.0}
        ]
        if fp16:
            try:
                from apex import amp
            except ImportError:
                raise ImportError("Please install apex from https://www.github.com/nvidia/apex to use fp16 training.")
            model, optimizer = amp.initialize(self.model, optimizer)

        # multi-gpu training (should be after apex fp16 initialization)
        if n_gpu > 1:
            model = torch.nn.DataParallel(self.model)

        # Distributed training (should be after apex fp16 initialization)
        if local_rank != -1:
            model = torch.nn.parallel.DistributedDataParallel(self.model, device_ids=[local_rank],
                                                              output_device=local_rank,
                                                              find_unused_parameters=True)

        # Train!
        logger.info("***** Running training *****")
        logger.info("  Num examples = %d", len(train_dataset))
        logger.info("  Num Epochs = %d", epochs)
        logger.info("  Total train batch size (w. parallel, distributed & accumulation) = %d",
                    batch_size * (
                        torch.distributed.get_world_size() if args.local_rank != -1 else 1))
        logger.info("  Gradient Accumulation steps = %d", args.gradient_accumulation_steps)
        logger.info("  Total optimization steps = %d", t_total)

        global_step = 0
        tr_loss, logging_loss = 0.0, 0.0
        self.model.zero_grad()
        train_iterator = trange(int(args.num_train_epochs), desc="Epoch", disable=args.local_rank not in [-1, 0])
        set_seed(args)  # Added here for reproductibility (even between python 2 and 3)
        for _ in train_iterator:
            epoch_iterator = tqdm(train_dataloader, desc="Iteration", disable=args.local_rank not in [-1, 0])
            for step, batch in enumerate(epoch_iterator):
                model.train()
                batch = tuple(t.to(args.device) for t in batch)
                inputs = {'input_ids': batch[0],
                          'attention_mask': batch[1],
                          'labels': batch[3]}
                if args.model_type != 'distilbert':
                    inputs['token_type_ids'] = batch[2] if args.model_type in ['bert',
                                                                               'xlnet'] else None  # XLM, DistilBERT and RoBERTa don't use segment_ids
                outputs = model(**inputs)
                loss = outputs[0]  # model outputs are always tuple in transformers (see doc)

                if args.n_gpu > 1:
                    loss = loss.mean()  # mean() to average on multi-gpu parallel training
                if args.gradient_accumulation_steps > 1:
                    loss = loss / args.gradient_accumulation_steps

                if args.fp16:
                    with amp.scale_loss(loss, optimizer) as scaled_loss:
                        scaled_loss.backward()
                    torch.nn.utils.clip_grad_norm_(amp.master_params(optimizer), args.max_grad_norm)
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)

                tr_loss += loss.item()
                if (step + 1) % args.gradient_accumulation_steps == 0:
                    optimizer.step()
                    scheduler.step()  # Update learning rate schedule
                    model.zero_grad()
                    global_step += 1

                    if args.local_rank in [-1, 0] and args.logging_steps > 0 and global_step % args.logging_steps == 0:
                        # Log metrics
                        if args.local_rank == -1 and args.evaluate_during_training:  # Only evaluate when single GPU otherwise metrics may not average well
                            results = evaluate(args, model, tokenizer)
                            for key, value in results.items():
                                tb_writer.add_scalar('eval_{}'.format(key), value, global_step)
                        tb_writer.add_scalar('lr', scheduler.get_lr()[0], global_step)
                        tb_writer.add_scalar('loss', (tr_loss - logging_loss) / args.logging_steps, global_step)
                        logging_loss = tr_loss

                    if args.local_rank in [-1, 0] and args.save_steps > 0 and global_step % args.save_steps == 0:
                        # Save model checkpoint
                        output_dir = os.path.join(args.output_dir, 'checkpoint-{}'.format(global_step))
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        model_to_save = model.module if hasattr(model,
                                                                'module') else model  # Take care of distributed/parallel training
                        model_to_save.save_pretrained(output_dir)
                        torch.save(args, os.path.join(output_dir, 'training_args.bin'))
                        logger.info("Saving model checkpoint to %s", output_dir)

                if args.max_steps > 0 and global_step > args.max_steps:
                    epoch_iterator.close()
                    break
            if args.max_steps > 0 and global_step > args.max_steps:
                train_iterator.close()
                break

        if args.local_rank in [-1, 0]:
            tb_writer.close()

        return global_step, tr_loss / global_step

    def eval(self):
        pass

    def run(self, *args):
        # Protobuffs in and protobuffs out
        batch = self.tokenizer(args[0], args[1])
        return self.model(batch)

    @staticmethod
    def architectures():
        return list(MODEL_CLASSES.keys())
