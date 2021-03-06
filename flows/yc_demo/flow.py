from koursaros.gnes_addons import Flow


flow = (
    Flow(with_frontend=False)
    .add_http_client(name='http')
    .add_frontend(copy_flow=False)
    .add_router(yaml_path='BaseRouter')
    .add_router(name='block', yaml_path='block_train.yml')
    .add_preprocessor(name='unary', yaml_path='text.yml', doc_type=1)
    .add_encoder(name='textbyte', yaml_path='max1024.yml')
    .add_indexer(name='whoosh', yaml_path='base.yml')
    .add_indexer(name='simple_dict', yaml_path='base.yml')
    .add_router(yaml_path='BaseRouter', recv_from=['Router0'])
    .add_router(name='rerank', yaml_path='base.yml', recv_from=['rocksdb', 'Router1'])
)
