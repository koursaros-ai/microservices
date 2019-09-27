from koursaros import Service

service = Service(__file__)


@service.stubs.piggify
def piggify(sentence, publish):
    pig_latin = [word[1:] + word[0] + "ay" for word in sentence.text.split()]
    service.messages.Piggified(
        sentence=sentence,
        pig_latin=' '.join(pig_latin)
    )
    publish(sentence)

