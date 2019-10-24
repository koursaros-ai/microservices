from koursaros.gnes_addons import Flow


flow = (
    Flow(check_version=True, with_frontend=False)
    .add_http_client(name='http') # builds but doesn't deploy
    .add_frontend(copy_flow=False)
    .add_router(yaml_path='BaseRouter')
    .add_encoder(name='textbyte', yaml_path='max256.yml')
    .add_indexer(name='keyword', yaml_path='base.yml') # aho corosick
    .add_router(yaml_path='BaseRouter', recv_from=['Router0'])
    .add_router(name='rerank', yaml_path='base.yml', recv_from=['keyword', 'Router1'])
)
