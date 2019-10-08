from koursaros.service import Service
from koursaros.modeling import model_from_config
from koursaros.utils.misc import batch_fn

service = Service()
model = model_from_config(service.service_yaml)

@service.stub
def rerank():

    def score(lines):
        claims = [claim_with_lines.claim.text] * len(lines)
        return regression_model.classify(claims, lines)
    results = []
    for scores, inputs in batch_fn(BATCH_SIZE, score, claim_with_lines.lines):
        for score, line in zip(scores, inputs):
            results.append((score, line))
    results.sort(key=lambda x: x[0], reverse=True)
    print("publishing")
