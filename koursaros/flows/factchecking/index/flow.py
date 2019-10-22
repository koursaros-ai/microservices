from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='postgres', yaml_path='hub/client/postgres/wikititles.yml')
    .add_preprocessor(name='sentsplit', replicas=2, storage='1Gi',
                      yaml_path='hub/preprocessor/sentsplit/jsonmode.yml')
    .add_encoder(name='textbyte', recv_from='sentsplit', replicas=2,
                 yaml_path='hub/encoder/textbyte/max256.yml')
    .add_indexer(name='keyword', replicas=2, yaml_path='hub/indexer/keyword/base.yml')
    .add_indexer(name='lvdb', recv_from='sentsplit', replicas=2,
                 yaml_path='hub/indexer/lvdb/base.yml')
    .add_router(name='reduce', num_part=2, recv_from=['keyword', 'lvdb'],
                yaml_path='BaseReduceRouter')
)

# checkout how the flow looks like (...and post it on Twitter, but hey what do I know about promoting OSS)
# funny!
