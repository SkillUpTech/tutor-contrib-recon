"""The Recon CLI definitions."""

import cloup

from tutor_recon.override.main import main_config
from tutor_recon.override.module import OverrideModule
from tutor_recon.util.cli import emit
from tutor_recon.util.paths import root_dirs
from tutor_recon.util.vjson import expand_references


@cloup.command(help="Remove a module by name.")
@cloup.argument("name")
@cloup.pass_context
def remove(context: cloup.Context, name: str):
    _, recon_root = root_dirs(context)
    modules_root = recon_root / "modules"
    module = OverrideModule.by_name(name, modules_root)
    main = main_config(recon_root)
    main.remove_where(**expand_references(module.to_object()))
    main.save(recon_root / "main.v.json")
    emit(
        f"Removed module '{name}' from the current configuration. To remove completely, delete the corresponding directory in {modules_root}."
    )


command = remove
