"""The Recon CLI definitions."""


import cloup
from cloup.constraints import mutually_exclusive


from tutor_recon.override.main import main_config
from tutor_recon.override.module import OverrideModule
from tutor_recon.override.sequence import OverrideSequence
from tutor_recon.util import vjson
from tutor_recon.util.paths import root_dirs


@cloup.command(help="Print the current recon configuration as JSON.", name="list")
@cloup.option_group(
    "Output data options",
    cloup.option(
        "--no-expand",
        is_flag=True,
        default=False,
        help="Don't expand references to files ('$+') into objects.",
    ),
    cloup.option(
        "--no-duplicates", is_flag=True, help="Remove entries which will ultimately be overwritten by later overrides, but preserve the structure of the output."
    ),
    cloup.option(
        "--compact", is_flag=True, help="Generate and display a single, combined top-level override for each file or template."
    ),
    cloup.option(
        "--claims", is_flag=True, help="Output an itemized list of all overriden options and files along with their final values."
    ),
    constraint=mutually_exclusive
)
@cloup.option_group(
    "Data source options",
    cloup.option(
        "--module", nargs=1, multiple=True, help="Only include overrides from the given module. Can be specified multiple times to include multiple modules."
    ),
)
@cloup.pass_context
def list_(context: cloup.Context, no_expand: bool, no_duplicates: bool, compact: bool, claims: bool, module: "list[str]"):
    _, recon_root = root_dirs(context)
    sequence = main_config(recon_root)
    modules_root = recon_root / "modules"
    if module:
        sequence = OverrideSequence([OverrideModule.by_name(name, modules_root) for name in module])
    if claims:
        config_str = vjson.dumps({".".join(k): v for k, v in sequence.claims.items()})
    else:
        config_str = vjson.dumps(sequence, expand_remote_mappings=(not no_expand), location=recon_root)
    print(config_str)


command = list_
