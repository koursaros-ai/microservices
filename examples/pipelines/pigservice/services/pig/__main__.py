

from koursaros.pipelines import pigservice

pipeline = pigservice(__file__)


@pipeline.services.pig.stubs.piggify
def piggify(sentence):
    print(sentence)
    pig_latin = [word[1:] + word[0] + "ay" for word in sentence.text.split()]
    piggified = pipeline.services.backend.stubs.receive.Piggified(
        sentence=sentence,
        pig_latin=' '.join(pig_latin)
    )
    pipeline.services.backend.stubs.receive(piggified)


if __name__ == "__main__":
    pipeline.services.pig.run()
