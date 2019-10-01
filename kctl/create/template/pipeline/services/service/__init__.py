from koursaros.pipelines import pipeline

example_pipeline = pipeline(__file__)
service = pipeline.services.service


@service.stubs.receive
def receive(note):
    print(f'Got notification!: {note}')


if __name__ == "__main__":
    if pipeline.args.connection == 'dev_local':
        print('Command line -c = dev_local')

    notification = service.stubs.receive.Notification(text='hello!')
    service.stubs.receive(notification)

