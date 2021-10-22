"""The Recon CLI definitions."""


import click
import cloup

from tutor_recon.util.paths import root_dirs


@cloup.command(help="Echo the location of the config overrides directory over stdout.")
@cloup.pass_context
def printroot(context: cloup.Context):
    _, recon_root = root_dirs(context)
    click.echo(recon_root.resolve())


command = printroot
