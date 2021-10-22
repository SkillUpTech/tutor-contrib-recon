"""The Recon CLI definition."""

import cloup
from importlib import import_module

from tutor_recon.util.constants import CONTEXT_SETTINGS, PROGRAM_DESCRIPTION

SUBCOMMANDS = (
    ".add_module",
    ".init",
    ".list_",
    ".new_module",
    ".printroot",
    ".replace_template",
    ".save",
    ".update_module",
)


@cloup.group(
    context_settings=CONTEXT_SETTINGS,
    help=PROGRAM_DESCRIPTION,
)
def recon():
    pass


for subcommand in SUBCOMMANDS:
    recon.add_command(import_module(subcommand, package=__package__).command)
