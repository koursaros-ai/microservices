# | APP         | MODEL     | REPS  | YAML_PATH         | IN            | OUT      | CMD
1 | httpclient  | http      | 1     |                   | RPC:          | RPC:2    |
2 | frontend    |           | 1     |                   | PULL:         | PUSH:    |
3 | router      |           | 1     | BaseRouter        | PULL:2        | PUB:     |
4 | router      | block     | 1     | block_train.yml   | SUB:3         | PUSH:    |
5 | preprocessor| unary     | 1     | text.yml          | PULL:4        | PUSH:    | doc_type=1
6 | encoder     | textbyte  | 1     | max1024.yml       | PULL:5        | PUSH:    |
7 | indexer     | whoosh    | 1     | base.yml          | SUB:6         | PUSH:2   |
8 | indexer     | keyword   | 1     | base.yml          | SUB:6         | PUSH:2   |
