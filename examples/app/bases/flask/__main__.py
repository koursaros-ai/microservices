from koursaros.service import Service
from flask import Flask, request, jsonify


service = Service()
app = Flask(__name__)

SUCCESS = dict(status='success')
FAILURE = dict(status='failure', msg='Please provide a msg')

@app.route('/')
def receive():
    text = request.args.get('q')
    if not text:
        return jsonify(FAILURE)

    send(service.Message(text=text))
    return jsonify(SUCCESS)


@service.stub
def send(msg):
    service.logger.info('Sending %s' % msg)
    return msg


if __name__ == "__main__":
    service.run(subs=[app.run])




