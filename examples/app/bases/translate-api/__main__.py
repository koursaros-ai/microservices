
from koursaros.service import Service
from googletrans import Translator

service = Service()
src_lang = service.yaml.src_lang
dest_lang = service.yaml.dest_lang
translator = Translator()


@service.stub
def translate(msg):
    return dict(text=translator.translate(msg.text))


if __name__ == "__main__":
    service.run()
