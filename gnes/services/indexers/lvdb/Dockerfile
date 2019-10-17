FROM gnes/hub-indexer:latest-lvdb-store

# placeholder to force rebuild
RUN echo 3

ADD *.yml ./

ENTRYPOINT ["gnes", "index", "--yaml_path", "lvdb.yml"]