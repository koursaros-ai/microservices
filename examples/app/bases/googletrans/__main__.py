
from koursaros.service import Service
from googletrans import Translator

service = Service()
dest_lang = service.yaml.dest_lang
translator = Translator()


@service.stub
def translate(translations):
    last_translation = translations.translations[-1]
    last_lang = last_translation.lang
    last_trans = last_translation.text
    new_trans = translations.translations.add()
    trans = translator.translate(last_trans, src=last_lang, dest=dest_lang).text
    new_trans.lang = dest_lang
    new_trans.text = trans
    return translations


if __name__ == "__main__":
    service.run()
