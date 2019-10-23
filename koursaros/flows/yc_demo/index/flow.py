from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='csv', yaml_path='base.yml') # builds but doesn't deploy
    .add_indexer(name='keyword', yaml_path='base.yml') # aho corosick
    .add_router(name='rerank', yaml_path='base.yml') # transformers
)
