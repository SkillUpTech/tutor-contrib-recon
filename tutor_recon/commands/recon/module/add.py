"""The Recon CLI definitions."""

from uuid import uuid4

import click
import cloup


from tutor_recon.override.main import main_config
from tutor_recon.override.reference import OverrideReference
from tutor_recon.util import vjson
from tutor_recon.util.cli import emit
from tutor_recon.util.module import (
    clone_repo,
    load_info,
    abort_if_exists,
)
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Clone a remote override module.")
@cloup.argument("url")
@cloup.pass_context
def add(context: cloup.Context, url: str):
    _, recon_root = root_dirs(context)
    modules_root = recon_root / "modules"
    repo_name = uuid4()
    clone_repo(name=repo_name, url=url, to=modules_root)
    module_root = modules_root / repo_name
    module_info = load_info(module_path=module_root / repo_name)
    module_name = module_info["name"]
    abort_if_exists(modules_root=modules_root, module_name=module_name)
    module_root.rename("module_name")
    emit(f"Cloned module to {click.style(module_root, fg='yellow')}.")
    module = vjson.load(module_root / "module.v.json", location=module_root)
    reference = OverrideReference(module)
    main = main_config(recon_root)
    main.add_override(reference)
    main.save(recon_root / "main.v.json")
    emit(f"Successfully applied {module_name} 👍")


command = add
