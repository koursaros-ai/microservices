import torch.hub
from koursaros.service import Service

service = Service()
pretrained = service.yaml.pretrained
model = torch.hub.load('pytorch/fairseq', pretrained, tokenizer='moses')

@service.stub
def translate(translate_query):
    return dict(
        text = model.translate(translate_query.text)
    )

if __name__ == '__main__':
    service.run()