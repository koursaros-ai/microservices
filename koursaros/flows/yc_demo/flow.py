from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client() # builds but doesn't deploy
    .add_router(yaml_path='BaseUnaryRouter')
    .add_encoder(name='textbyte', yaml_path='max256.yml', recv_from=['pubber'])
    .add_indexer(name='keyword', yaml_path='base.yml') # aho corosick
    .add_router(yaml_path='BaseUnaryRouter', recv_from=['pubber'])
    .add_router(name='rerank', yaml_path='base.yml', recv_from=['keyword', 'reroute'])
)
