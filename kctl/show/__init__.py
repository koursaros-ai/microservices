

import webbrowser
from ..decorators import *


@click.group()
def show():
    """Show gnes architecture."""


@show.command()
@pipeline_options
def pipeline(app_manager, pipeline_name, runtime):
    """Deploy a pipeline with compose or k8s. """
    url = app_manager.get_flow('pipelines', pipeline_name, runtime).build().to_url()

    try:
        webbrowser.open_new_tab(url)
    except webbrowser.Error as ex:
        app_manager.logger.critical(
            '%s\nCould not open browser... Please visit:\n%s' % (ex, url))
