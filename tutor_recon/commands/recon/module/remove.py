"""The Recon CLI definitions."""

import cloup

from tutor_recon.util.cli import emit

from .disable import disable

from tutor_recon.util.module import remove_module
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Disable (if applicable) and remove a module.")
@cloup.argument("name")
@cloup.pass_context
def remove(context: cloup.Context, name: str):
    _, recon_root = root_dirs(context)
    modules_root = recon_root / "modules"
    context.invoke(disable, name=name)
    remove_module(modules_root=modules_root, name=name)
    emit(f"Removed module '{name}'.")


command = remove
