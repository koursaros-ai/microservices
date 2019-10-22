from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='postgres', yaml_path='clients/postgres/wiki_titles.yml')
    .add_preprocessor(name='sent_split', replicas=2,
                      yaml_path='services/preprocessors/sent_split/json_mode.yml')
    .add_encoder(name='text_byte', recv_from='sent_split', replicas=2,
                 yaml_path='services/encoders/text_byte/max_256.yml')
    .add_indexer(name='keyword', replicas=2,
                 yaml_path='services/indexers/keyword/base.yml')
    .add_indexer(name='lvdb', replicas=2, yaml_path='services/indexers/lvdb/base.yml')
    .add_encoder(name='roberta_infer', replicas=2,
                 yaml_path='services/encoders/roberta_infer/dim_64.yml')
    .add_router(name='reduce', num_part=2, yaml_path='BaseReduceRouter')
)


# checkout how the flow looks like (...and post it on Twitter, but hey what do I know about promoting OSS)
# funny!
