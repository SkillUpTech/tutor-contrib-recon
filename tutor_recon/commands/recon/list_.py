"""The Recon CLI definitions."""


import cloup


from tutor_recon.override.main import main_config
from tutor_recon.util import vjson
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Print the current recon configuration as JSON.", name="list")
@cloup.option_group(
    "Output Format",
    cloup.option(
        "--expand/--no-expand",
        is_flag=True,
        default=True,
        help="Expand references to files ('$+') into objects.",
    ),
    cloup.option(
        "--effective", is_flag=True, help="[WIP] When a value or file is overridden multiple times, only show the final override. Implies --expand."
    ),
    cloup.option(
        "--compact", is_flag=True, help="[WIP] Generate and display a single, combined top-level override for each file or template. Implies --effective."
    ),
    cloup.option(
        "--claims", is_flag=True, help="[WIP] Generate a flat list of all overriden options and files along with their ultimate terminal values."
    ),
)
@cloup.option(
    "--module", nargs=1, multiple=True, help="[WIP] Only include overrides from the given module. Can be specified multiple times to include multiple modules."
)
@cloup.pass_context
def list_(context: cloup.Context, expand: bool, effective: bool, compact: bool, module: list):
    _, recon_root = root_dirs(context)
    main = main_config(recon_root)
    config_str = vjson.dumps(main, expand_remote_mappings=expand, location=recon_root)
    print(config_str)


command = list_
