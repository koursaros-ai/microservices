def decorator_group(decorators):
    """returns a decorator which bundles the given decorators

    :param decorators: iterable of decorators
    :return: single decorator

    Example:
        deploy_options = decorator_group([
            click.option('-c', '--connection', required=True),
            click.option('-r', '--rebind', is_flag=True),
            click.option('-d', '--debug', is_flag=True),
        ])

    """
    def group(f):
        for decorator in decorators:
            f = decorator(f)
        return f
    return group
