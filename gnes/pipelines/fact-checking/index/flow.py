from gnes.flow import Flow

flow = (
    Flow(check_version=True)
    .add_preprocessor(name='SentSplitPrep', replicas=2,
                      yaml_path='../../../services/preprocessors/sent-split/json-mode.yml')
    .add_encoder(name='SiameseBertEncoder', replicas=2,
                 yaml_path='../../../services/encoders/siamese-bert/dim-64.yml')
    .add_indexer(name='FaissIdx', replicas=2,
                 yaml_path='../../../services/indexers/faiss-cpu/base.yml')
    .add_encoder(name='TextByteEncoder', recv_from='SentSplitPrep', replicas=2,
                 yaml_path='../../../services/encoders/text-byte/max-256.yml')
    .add_indexer(name='KeywordIdx', replicas=2,
                 yaml_path='../../../services/indexers/keyword/base.yml')
    .add_indexer(name='LevelDBIdx', recv_from='SentSplitPrep', replicas=2,
                 yaml_path='../../../services/indexers/lvdb/base.yml')
    .add_router(name='Reduce', num_part=2, yaml_path='BaseReduceRouter',
                recv_from=['FaissIdx', 'KeywordIdx', 'LevelDBIdx'])
)

# checkout how the flow looks like (...and post it on Twitter, but hey what do I know about promoting OSS)
# funny!
