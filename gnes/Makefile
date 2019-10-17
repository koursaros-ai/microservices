
build_postgres_client: ; cd clients/postgres && docker build -t clients:postgres .

clean_cache: ; rm -rf cache && mkdir -p cache
clean_down: ; ls #docker-compose down

wait: ; @printf "sleep 15s for docker to recycle network resources...\n"; sleep 1

deploy_fact_index: ; docker-compose -f pipelines/fact-checking/index-compose.yml up
fact_client_index: ; docker run --network=host -it koursaros/gnes-fever:train-client \
    --mode index --verbose --cred_repo $(cred_repo) --cred_user $(cred_user) \
    --cred_pass $(cred_pass) --limit 100
fact_index: clean_cache clean_down wait deploy_fact_index