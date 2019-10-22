## Push Pipeline
1. Set environment variables:

1. Compile `koursaros.proto` located in `koursaros/protos`
2. Check `actions.yaml`
    - [x] check syntax
    - [x] check naming conventions
    - [x] check each returning stub has a valid receving pin
    - [x] check that all microservices are receiving (except externals)
    - [x] check each mentioned proto is compiled
    - [x] check each sent proto type == recevied proto type
    - [x] check each mentioned microservice exists
    - [x] check stub functions exist in microservices
3. Check microservices
    - [ ] each returning stub publishes
    - [ ] microservices do not use invalid proto attributes
4. Recreate RabbitMQ bindings
    - [x] check that connection in `koursaros.yaml` exists
    - [x] check admin plugin exists
    - [x] check admin login permissions
    - [x] bind according to `actions.yaml`
5. Build microservices
   - if (detect changes in microservice directory or `koursaros.yaml`):
        - if (external microservice):
            - [ ] remove build directory
        - if (not external microservice):
            - [ ] add changes to git
            - [x] build dockerfile
            - [x] build deployment
            - [x] build cloudbuild
    - [x] git commit/push with predefined commit sha
    - [ ] push cloudbuild to rest api 