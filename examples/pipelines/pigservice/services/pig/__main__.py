

from koursaros.pipelines import pigservice

service = Service(__file__)


@service.stub('piggify')
def piggify(sentence, publish):
    pig_latin = [word[1:] + word[0] + "ay" for word in sentence.text.split()]
    piggified = service.messages.Piggified(
        sentence=sentence,
        pig_latin=' '.join(pig_latin)
    )
    publish(piggified)

if __name__ == "__main__":
    service.run()
