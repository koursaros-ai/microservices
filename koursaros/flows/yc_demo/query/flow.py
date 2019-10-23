from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='csv', yaml_path='base.yml')
    .add_encoder(name='textbyte', yaml_path='max256.yml')
    .add_indexer(name='keyword',yaml_path='base.yml')
    .add_router(name='rerank', yaml_path='base.yml')
)
