from koursaros.gnes_addons import Flow

flow = (
    Flow(check_version=True)
    .add_client(name='postgres', yaml_path='client/postgres/testrerank.yml')
    .add_indexer(name='keyword',yaml_path='indexer/keyword/base.yml')
    .add_router(name='rerank', yaml_path='router/rerank/base.yml')
)
