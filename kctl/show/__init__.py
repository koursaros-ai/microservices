
import click
import webbrowser


@click.group()
def show():
    """Show gnes architecture."""


@show.command()
@click.argument('pipeline_name')
@click.argument('-r', '--runtime', required=True)
@click.pass_obj
def pipeline(app_manager, pipeline_name, runtime):
    """Deploy a pipeline with compose or k8s. """
    build = app_manager.get_flow('pipelines', pipeline_name, runtime)
    url = build.to_url()

    try:
        webbrowser.open_new_tab(url)
    except webbrowser.Error as ex:
        app_manager.logger.critical(
            '%s\nCould not open browser... Please visit:\n%s' % (ex, url))
