"""The Recon CLI definitions."""

import cloup

from tutor_recon.override.main import main_config
from tutor_recon.override.module import OverrideModule
from tutor_recon.util.cli import emit
from tutor_recon.util.paths import root_dirs
from tutor_recon.util.vjson import expand_references


@cloup.command(help="Disable the module with the given name.")
@cloup.argument("name")
@cloup.pass_context
def disable(context: cloup.Context, name: str):
    _, recon_root = root_dirs(context)
    modules_root = recon_root / "modules"
    module = OverrideModule.by_name(name, modules_root)
    main = main_config(recon_root)
    main.remove_where(**expand_references(module.to_object()))
    main.save(recon_root / "main.v.json")
    emit(f"Disabled module '{name}'.")


command = disable
