from koursaros.service import Service
from koursaros.modeling import model_from_config

service = Service()
model = model_from_config(service.service_yaml)

@service.stub
def classify(text_query):
    label = model.run(*text_query.text)
    return service.Message(
        text=text_query.text,
        label=label
    )

if __name__ == "__main__":
    service.run()
