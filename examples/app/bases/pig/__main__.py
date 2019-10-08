
from koursaros.service import Service

service = Service()


@service.stub
def piggify(msg):
    pig_latin = ' '.join([word[1:] + word[0] + "ay" for word in msg.text.split()])
    return service.Message(text=pig_latin)


if __name__ == "__main__":
    service.run()
