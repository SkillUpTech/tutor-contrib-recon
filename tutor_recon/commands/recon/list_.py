"""The Recon CLI definitions."""


import cloup


from tutor_recon.config.main import main_config
from tutor_recon.util import vjson
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Print the current recon configuration as JSON.", name="list")
@cloup.option(
    "--expand/--no-expand",
    is_flag=True,
    default=True,
    help="Expand references to files ('$+') into objects.",
)
@cloup.pass_context
def list_(context: cloup.Context, expand: bool):
    _, recon_root = root_dirs(context)
    main = main_config(recon_root)
    config_str = vjson.dumps(main, expand_remote_mappings=expand, location=recon_root)
    print(config_str)


command = list_
