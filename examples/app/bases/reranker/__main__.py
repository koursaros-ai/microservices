from koursaros.utils.misc import batch_fn
from koursaros.service import Service
from koursaros.modeling import model_from_config

service = Service()
model = model_from_config(service.service_yaml)

@service.stub
def rerank(rerank_query):
    results = [(model.run(rerank_query.query, line.text), line) for line in rerank_query.lines]
    results.sort(key=lambda x: x[0], reverse=True)
    return service.Message(
        query = rerank_query.query,
        lines=[line[1] for line in results]
    )

if __name__ == "__main__":
    service.run()

