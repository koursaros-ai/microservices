

from koursaros.pipelines import pig_pipeline

pipeline = pig_pipeline(__package__)

backend = pipeline.services.backend
pig = pipeline.services.pig


@pig.stubs.piggify
def piggify(sentence):
    print(sentence)
    pig_latin = [word[1:] + word[0] + "ay" for word in sentence.text.split()]
    piggified = backend.stubs.receive.Piggified(
        sentence=sentence,
        pig_latin=' '.join(pig_latin)
    )
    backend.stubs.receive(piggified)


if __name__ == "__main__":
    pig.run()
