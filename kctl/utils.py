
BOLD = '\033[1m{}\033[0m'


def decorator_group(options):
    """returns a decorator which bundles the given decorators

    :param options: iterable of decorators
    :return: single decorator

    Example:
        deploy_options = option_group([
            click.option('-c', '--connection', required=True),
            click.option('-r', '--rebind', is_flag=True),
            click.option('-d', '--debug', is_flag=True),
        ])

    """
    def option_decorator(f):
        for option in options:
            f = option(f)
        return f
    return option_decorator