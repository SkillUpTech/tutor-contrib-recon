"""The Recon CLI definitions."""

import cloup

from tutor_recon.override.main import main_config
from tutor_recon.util.module import get_reference
from tutor_recon.util.cli import emit
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Enable a module which has already been downloaded.")
@cloup.argument("name")
@cloup.pass_context
def enable(context: cloup.Context, name: str):
    _, recon_root = root_dirs(context)
    modules_root = recon_root / "modules"
    reference = get_reference(modules_root=modules_root, name=name)
    main = main_config(recon_root)
    main.add_override(reference)
    main.save(recon_root / "main.v.json")
    emit(f"Successfully enabled {name}.")


command = enable
