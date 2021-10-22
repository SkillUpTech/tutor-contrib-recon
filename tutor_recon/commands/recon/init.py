from pathlib import Path

import click
import cloup

from tutor_recon.config.main import scaffold_all
from tutor_recon.util.cli import emit
from tutor_recon.util.paths import overrides_path
from tutor_recon.util.tutor import run_tutor_config_save


@cloup.command(help="Initialize recon.")
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


command = init
