

from koursaros.pipelines import pig_pipeline

Pipline = pig_pipeline(__package__)

backend = Pipline.Services.backend
pig = Pipline.Services.pig


@pig.Stubs.piggify
def piggify(sentence):
    print(sentence)
    pig_latin = [word[1:] + word[0] + "ay" for word in sentence.text.split()]
    piggified = backend.Stubs.receive.Piggified(
        sentence=sentence,
        pig_latin=' '.join(pig_latin)
    )
    return piggified


if __name__ == "__main__":
    pig.run()
