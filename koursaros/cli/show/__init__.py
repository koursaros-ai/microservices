

import webbrowser
import click


@click.group()
def show():
    """Show gnes architecture."""


@show.command()
@click.argument('flow_name')
@click.pass_obj
def flow(app_manager, flow_name):
    """Deploy a pipeline with compose or k8s. """
    url = app_manager.get_flow(flow_name).build().to_url()

    try:
        webbrowser.open_new_tab(url)
    except webbrowser.Error as ex:
        app_manager.logger.critical(
            '%s\nCould not open browser... Please visit:\n%s' % (ex, url))
