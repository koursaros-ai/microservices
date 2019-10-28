# | APP         | MODEL     | REPS  | YAML_PATH         | IN        | OUT      | CMD
1 | httpclient  | http      | 1     |                   | RPC:      | RPC:2    |
2 | frontend    |           | 1     |                   | PULL:     | PUSH:    | frontend
3 | router      |           | 1     | BaseRouter        | PULL:2    | PUB:     | route
4 | router      | block     | 1     | block_train.yml   | SUB:3     | PUSH:    |
5 | preprocessor| unary     | 1     | text.yml          | PULL:4    | PUSH:    |
6 | encoder     | textbyte  | 1     | max1024.yml       | PULL:5    | PUSH:    |
7 | indexer     | whoosh    | 1     | base.yml          | PULL:6    | PUSH:    |
8 | indexer     | rocksdb   | 1     | base.yml          | PULL:7    | PUSH:2   |
