from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='postgres', yaml_path='clients/postgres/wikititles.yml')
    .add_preprocessor(name='sentsplit', replicas=2,
                      yaml_path='services/preprocessors/sentsplit/jsonmode.yml')
    .add_encoder(name='textbyte', recv_from='sentsplit', replicas=2,
                 yaml_path='services/encoders/textbyte/max256.yml')
    .add_indexer(name='keyword', replicas=2,
                 yaml_path='services/indexers/keyword/base.yml')
    .add_indexer(name='lvdb', replicas=2, yaml_path='services/indexers/lvdb/base.yml')
    .add_encoder(name='robertainfer', replicas=2,
                 yaml_path='services/encoders/robertainfer/dim64.yml')
    .add_router(name='reduce', num_part=2, yaml_path='BaseReduceRouter')
)


# checkout how the flow looks like (...and post it on Twitter, but hey what do I know about promoting OSS)
# funny!
