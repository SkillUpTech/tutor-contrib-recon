"""The Recon CLI definitions."""

from pathlib import Path

import cloup


from tutor_recon.override.main import main_config
from tutor_recon.override.reference import OverrideReference
from tutor_recon.override.module import OverrideModule
from tutor_recon.util.cli import emit
from tutor_recon.util.module import init_repo
from tutor_recon.util.paths import root_dirs
from tutor_recon.util.vjson.reference import RemoteMapping


@cloup.command(help="Create a new override module with the given name.")
@cloup.option(
    "--git-url",
    metavar="URL",
    default=None,
    help="The URL to a git repository where you plan to host this module.",
)
@cloup.option(
    "--initialize-repo/--no-initialize-repo",
    is_flag=True,
    default=True,
    help="Create/don't create a git repository. If --git-url is provided, set origin to the URL.",
)
@cloup.option(
    "--push/--no-push",
    is_flag=True,
    default=True,
    help="Push the initialized repository to origin if applicable.",
)
@cloup.argument("name", metavar="MODULE_NAME")
@cloup.pass_context
def new_module(
    context: cloup.Context, name: str, git_url: str, initialize_repo: bool, push: bool
):
    tutor_root, recon_root = root_dirs(context)
    modules_root = recon_root / Path("modules")
    module_root = Path("modules") / name
    target = module_root / "module.v.json"
    main = main_config(recon_root)
    module = OverrideModule.from_object(
        RemoteMapping(
            remote_reference=target,
            overrides=[],
            info=RemoteMapping(
                remote_reference=Path("module-info.json"), version="0.0.0", name=name
            ),
        )
    )
    reference = OverrideReference(module)
    main.add_override(reference)
    reference.scaffold(tutor_root, recon_root)
    main.save(recon_root / "main.v.json")
    if initialize_repo:
        init_repo(parent_dir=modules_root, name=name, url=git_url, push=push)
    emit(f"Created new override module at {target} 👍")


command = new_module
