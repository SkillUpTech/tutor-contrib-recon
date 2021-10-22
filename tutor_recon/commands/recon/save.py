"""The Recon CLI definitions."""

import cloup

from tutor_recon.util.tutor import run_tutor_config_save
from tutor_recon.config.main import override_all
from tutor_recon.util.cli import emit
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Apply all override settings to the rendered environment.")
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


command = save
