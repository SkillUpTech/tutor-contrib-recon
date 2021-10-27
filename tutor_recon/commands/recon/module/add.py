"""The Recon CLI definitions."""

import cloup

from tutor_recon.override.main import main_config
from tutor_recon.override.reference import OverrideReference
from tutor_recon.util.cli import emit
from tutor_recon.util.module import add_module
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Clone a remote override module.")
@cloup.argument("url")
@cloup.pass_context
def add(context: cloup.Context, url: str):
    _, recon_root = root_dirs(context)
    modules_root = recon_root / "modules"
    module = add_module(modules_root, url)
    reference = OverrideReference(module)
    main = main_config(recon_root)
    main.add_override(reference)
    main.save(recon_root / "main.v.json")
    emit(f"Successfully added and applied {url} 👍")


command = add
