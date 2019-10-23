from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='excel', yaml_path='testrerank.yml') # builds but doesn't deploy
    .add_indexer(name='keyword', yaml_path='base.yml')
    .add_router(name='rerank', yaml_path='base.yml')
)
