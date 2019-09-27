from koursaros import Service

service = Service(__file__)


@service.stub
def piggify(sentence, publish):
    pig_latin = [word[1:] + word[0] + "ay" for word in sentence.text.split()]
    piggified = service.messages.Piggified(
        sentence=sentence,
        pig_latin=' '.join(pig_latin)
    )
    publish(piggified)


def main():
    threads = service.run()

    for t in threads:
        t.start()

    for t in threads:
        t.join()