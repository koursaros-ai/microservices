
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
  template:
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

DESCRIPTION = '''kctl controls the \033[1;4mKoursaros\033[0m microservice platform.
Find more information at: https://github.com/koursaros-ai/koursaros

'''
PUSH = 'Check configuration yamls, bind rabbitmq, and deploy'
CREATE = 'Create boilerplate microservice'
PROTOC = 'Compile protos'
UNTRIGGER = 'Remove the auto-deployment triggers for a microservice'
