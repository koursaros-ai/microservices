from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='postgres', yaml_path='wiki-titles.yml')
    .add_preprocessor(name='sent_split', replicas=2, yaml_path='json-mode.yml')
    .add_encoder(name='siamese_bert', replicas=2, yaml_path='dim-64.yml')
    .add_indexer(name='faiss_cpu', replicas=2, yaml_path='base.yml')
    .add_encoder(name='text_byte', recv_from='sent-split', replicas=2, yaml_path='max-256.yml')
    .add_indexer(name='keyword', replicas=2, yaml_path='base.yml')
    .add_indexer(name='lvdb', recv_from='SentSplitPrep', replicas=2, yaml_path='base.yml')
    .add_router(name='Reduce', num_part=2, yaml_path='BaseReduceRouter',
                recv_from=['faiss-cpu', 'keyword', 'lvdb'])
)


# checkout how the flow looks like (...and post it on Twitter, but hey what do I know about promoting OSS)
# funny!
