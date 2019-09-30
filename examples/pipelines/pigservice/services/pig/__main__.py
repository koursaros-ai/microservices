

from koursaros.pipelines import pigservice

pipeline = pigservice(__file__)

piggfy_stub = pipeline.services.pig.stubs.piggify
receive_stub = pipeline.services.backend.stubs.receive


@piggfy_stub
def piggify(sentence):
    pig_latin = [word[1:] + word[0] + "ay" for word in sentence.text.split()]
    piggified = receive_stub.Piggified(
        sentence=sentence,
        pig_latin=' '.join(pig_latin)
    )
    receive_stub(piggified)


if __name__ == "__main__":
    pipeline.services.pig.run()
