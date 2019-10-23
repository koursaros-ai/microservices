from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='csv', yaml_path='base.yml') # builds but doesn't deploy
    .add_router(name='pubber', yaml_path='base.yml')
    .add_encoder(name='textbyte', yaml_path='max256.yml', recv_from=['pubber'])
    .add_indexer(name='keyword', yaml_path='base.yml') # aho corosick
    .add_router(name='reroute', yaml_path='base.yml', recv_from=['pubber'])
    .add_router(name='rerank', yaml_path='base.yml', recv_from=['keyword', 'reroute'])
)
