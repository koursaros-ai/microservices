
## Description

This module allows you to pull secure credentials into your python
script. It assumes that you create a private git repository with
your credentials in them prior to using get_creds().

## At a glance 

You can create a repository that looks like this:

```
creds
├── creds.yaml
├── google
│   └── bluehat.json
└── postgres
    └── postgres.pem
```

And a `creds.yaml` that looks like this:
```yaml
creds:
  postgres:
    host: !!str 12.345.678.910
    username: !!str postgres
    password: !!str my_password
    replicas: !!int 5
    dbname: !!str fever
    sslmode: !!str verify-ca
    sslrootcert: !file postgres/postgres.pem
  google:
    app_creds: !file google/bluehat.json
```

Let's say the repo you make is `madhatter/creds`.
You can get your credentials in a python script by doing the following:
```python
from koursaros.credentials import get_creds

creds = get_creds('madhatter/creds', username='alice', password='cheshire')
# NOTE: you don't need to log in if your git credentials are stored locally

# the !! denotes native python types. You can access them like:
creds.postgres.password # my_password
creds.postgres.replicas # 5

# the special !file tag means that it is a file. You can access
# three attributes from file objects (path, bytes, text):
creds.google.app_creds.path # '/absolute/path/to/google/app_creds/bluehat.json'
creds.google.app_creds.bytes # b'{"client_id": "293480342342034"}'
creds.google.app_creds.text # '{"client_id": "293480342342034"}'
```