import click


@click.group()
def save():
    """Save gnes deployment as swarm, minikube, k8s, or shell."""


@save.command()
@click.argument('pipeline_name')
@click.option('-r', '--runtime', required=True)
@click.option('-p', '--platform', required=True, default='minikube',
              type=click.Choice(['k8s', 'swarm', 'shell']))
@click.pass_obj
def pipeline(app_manager, pipeline_name, runtime, platform):
    """Deploy a pipeline with compose or k8s. """
    flow = app_manager.get_flow('pipelines', pipeline_name, runtime)
    globals()[platform](flow.build(), app_manager.logger.critical)


def swarm(flow, log):
    out_path = flow.path.parent.joinpath('docker-compose-temp.yml')
    out_path.write_text(flow.to_swarm_yaml())
    log('Saved swarm yaml to %s' % str(out_path))


def k8s(flow, log):
    for k, v in flow._service_nodes.items():
        log(k)
        log(v)
    import pdb
    pdb.set_trace()
