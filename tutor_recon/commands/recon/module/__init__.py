"""The Recon CLI definition."""

import cloup
from importlib import import_module

SUBCOMMANDS = (
    ".add",
    ".remove",
    ".new",
    ".update",
    ".disable",
    ".restore",
)


@cloup.group(
    help="Create, download, or update a recon module.",
)
def module():
    pass


for subcommand in SUBCOMMANDS:
    module.add_command(import_module(subcommand, package=__package__).command)

command = module
