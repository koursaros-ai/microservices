
CLOUDBUILD_TEMPLATE = '''
steps:  
- name: 'gcr.io/cloud-create/docker'
  args: ['build','-t','{image}:{tag}','-f','/workspace/koursaros/microservices/{microservice}/transpiled/Dockerfile','.']

- name: 'gcr.io/cloud-create/docker'
  args: ['push','{image}:{tag}']

- name: 'gcr.io/cloud-create/kubectl'
  id: Deploy
  args:
  - 'apply'
  - '-f'
  - 'deployment.yaml'
  env:
  - 'CLOUDSDK_COMPUTE_ZONE={zone}'
  - 'CLOUDSDK_CONTAINER_CLUSTER={cluster}'
  dir: 'koursaros/microservices/{microservice}/transpiled'
'''

DEPLOYMENT_TEMPLATE = '''
apiVersion: "apps/v1"
kind: "Deployment"
metadata:
  name: "{microservice}"
  namespace: "default"
  labels:
    app: "{microservice}"
spec:
  replicas: {replicas}
  strategy:
    type: {strategy_type}
  selector:
    matchLabels:
      app: "{microservice}"
  fact-checking:
    metadata:
      labels:
        app: "{microservice}"
    spec:
      nodeSelector:
        {node_selector}
      containers:
      - name: "{microservice}"
        image: "{image}:{tag}"
        resources:
          limits:
            {resource_limits}
'''

PVC_TEMPLATE = '''
        volumeMounts:
        - name: {volume}
          mountPath: /app/
      volumes:
      - name: {volume}
        persistentVolumeClaim:
          claimName: {volume}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {volume}
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: {size}
  storageClassName: standard
'''

DOCKERFILE_TEMPLATE = '''
FROM {image}

# move executable
ADD . /opt/koursaros
WORKDIR /opt/koursaros

# set args to env variables
{envs}

# install deps
{deps}

ENTRYPOINT {entrypoint}
'''
