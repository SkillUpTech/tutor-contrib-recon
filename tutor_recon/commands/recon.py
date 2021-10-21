"""The Recon CLI definitions."""

import json
from pathlib import Path
from uuid import uuid4

import click
import cloup


from tutor_recon.commands.tutor import tutor_config_save
from tutor_recon.config.main import main_config, override_all, scaffold_all
from tutor_recon.config.override_reference import OverrideReference
from tutor_recon.config.override_module import OverrideModule
from tutor_recon.config.templates import TemplateOverride
from tutor_recon.util import vjson
from tutor_recon.util.cli import emit
from tutor_recon.util.constants import (
    CONFIG_SAVE_STYLED,
    CONTEXT_SETTINGS,
    PROGRAM_DESCRIPTION,
    RECON_SAVE_STYLED,
)
from tutor_recon.util.module import (
    clone_repo,
    init_repo,
    load_info,
    pull_repo,
    abort_if_exists,
)
from tutor_recon.util.paths import overrides_path, root_dirs
from tutor_recon.util.vjson.reference import RemoteMapping


def run_tutor_config_save(context: cloup.Context) -> None:
    emit(f"Running {CONFIG_SAVE_STYLED}.")
    context.invoke(tutor_config_save)


@cloup.group(
    context_settings=CONTEXT_SETTINGS,
    help=PROGRAM_DESCRIPTION,
)
def recon():
    pass


@recon.command(help="Initialize recon.")
@cloup.option(
    "--env-dir",
    help="The path to where your environment override files should (or already do) reside.",
    type=cloup.Path(file_okay=False, path_type=Path),
    default=None,
)
@cloup.option(
    "--tutor/--no-tutor",
    is_flag=True,
    default=True,
    help="Run/don't run 'tutor config save' prior to applying overrides.",
)
@cloup.pass_context
def init(context: cloup.Context, env_dir, tutor):
    tutor_root = Path(context.obj.root)
    recon_root = overrides_path(tutor_root=tutor_root, env_dir=env_dir).resolve()
    if tutor:
        run_tutor_config_save(context)
    scaffold_all(tutor_root, recon_root)
    recon_root_str = click.style(str(recon_root), fg="magenta")
    emit(
        f"You're all set! Your environment overrides can be configured at {recon_root_str} 👍"
    )


@recon.command(help="Echo the location of the config overrides directory over stdout.")
@cloup.pass_context
def printroot(context: cloup.Context):
    _, recon_root = root_dirs(context)
    click.echo(recon_root.resolve())


@recon.command(help="Apply all override settings to the rendered environment.")
@cloup.option(
    "--tutor/--no-tutor",
    is_flag=True,
    default=True,
    help="Run/don't run 'tutor config save' prior to applying overrides.",
)
@cloup.pass_context
def save(context: cloup.Context, tutor):
    tutor_root, recon_root = root_dirs(context)
    if tutor:
        run_tutor_config_save(context)
    emit("Applying overrides.")
    override_all(tutor_root, recon_root)
    emit("Done.")


@recon.command(help="Scaffold an override of a tutor template in its entirety.")
@cloup.argument("path", metavar="PATH_RELATIVE_TO_ENV")
@cloup.pass_context
def replace_template(context: cloup.Context, path: str):
    tutor_root, recon_root = root_dirs(context)
    main = main_config(recon_root)
    override = TemplateOverride.for_template(Path(path))
    main.add_override(override)
    override.scaffold(tutor_root, recon_root)
    main.save(recon_root / "main.v.json")
    path_styled = click.style(str(path), fg="blue")
    override_styled = click.style(str(recon_root / override.src), fg="magenta")
    emit(f"Scaffolded {path_styled} at {override_styled} 👍")
    emit(
        f"Change the file to your heart's content, then it will be rendered when you run {RECON_SAVE_STYLED}."
    )


@recon.command(help="Print the current recon configuration as JSON.")
@cloup.option(
    "--expand/--no-expand",
    is_flag=True,
    default=True,
    help="Expand references to files ('$+').",
)
@cloup.pass_context
def list(context: cloup.Context, expand: bool):
    _, recon_root = root_dirs(context)
    main = main_config(recon_root)
    config_str = vjson.dumps(main, expand_remote_mappings=expand, location=recon_root)
    print(config_str)


@recon.command(help="Create a new override module with the given name.")
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
        vjson.RemoteMapping(
            target=target,
            info=RemoteMapping(target="module-info.json", version="0.0.0", name=name),
        )
    )
    reference = OverrideReference(module)
    main.add_override(reference)
    reference.scaffold(tutor_root, recon_root)
    main.save(recon_root / "main.v.json")
    if initialize_repo:
        init_repo(parent_dir=modules_root, name=name, url=git_url, push=push)
    emit(f"Created new override module at {target} 👍")


@recon.command(help="Clone a remote override module.")
@cloup.argument("url")
@cloup.pass_context
def add_module(context: cloup.Context, url: str):
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


@recon.command(help="Update an installed override module.")
@cloup.argument("name")
@cloup.pass_context
def update_module(context: cloup.Context, name: str):
    _, recon_root = root_dirs(context)
    module_path = recon_root / "modules" / name
    prev_info = load_info(module_path=module_path)
    pull_repo(loc=module_path)
    new_info = load_info(module_path=module_path)
    main = main_config(recon_root)
    main.save(recon_root / "main.v.json")
    emit(
        f"Updated {click.style(name, 'magenta')} from {prev_info['version']} to {new_info['version']}."
    )
