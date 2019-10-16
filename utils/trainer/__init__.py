from koursaros.modeling import model_from_yaml

def train(file):
    model = model_from_yaml(file, training=True)
    model.train()