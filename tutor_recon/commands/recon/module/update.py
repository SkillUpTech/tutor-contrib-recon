"""The Recon CLI definitions."""


import click
import cloup


from tutor_recon.override.main import main_config
from tutor_recon.util.cli import emit
from tutor_recon.util.module import (
    load_info,
    pull_repo,
)
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Update an installed override module.")
@cloup.argument("name")
@cloup.pass_context
def update(context: cloup.Context, name: str):
    _, recon_root = root_dirs(context)
    module_path = recon_root / "modules" / name
    prev_info = load_info(module_dir=module_path)
    pull_repo(loc=module_path)
    new_info = load_info(module_dir=module_path)
    main = main_config(recon_root)
    main.save(recon_root / "main.v.json")
    prev_version, new_version = prev_info["version"], new_info["version"]
    emit(
        f"Updated {click.style(name, 'magenta')} from {prev_version} to {new_version}."
    )


command = update
