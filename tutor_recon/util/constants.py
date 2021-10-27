import json

import click
import cloup

MAIN_COLOR = cloup.Color.bright_blue
ACCENT_COLOR = cloup.Color.magenta
EXTERNAL_COLOR = cloup.Color.yellow

HELP_EXAMPLE = click.style("tutor recon COMMAND --help", fg=MAIN_COLOR)
PROJECT_STYLED = click.style("tutor-contrib-recon", fg=ACCENT_COLOR)
PROGRAM_DESCRIPTION = f"""
{PROJECT_STYLED} -- Easily override Tutor settings and templates.

Use {HELP_EXAMPLE} for help with a particular subcommand.
"""

CONTEXT_SETTINGS = cloup.Context.settings(
    formatter_settings=cloup.HelpFormatter.settings(
        max_width=160,
        theme=cloup.HelpTheme(
            heading=cloup.Style(bold=True),
            invoked_command=cloup.Style(fg=MAIN_COLOR),
            col1=cloup.Style(fg=MAIN_COLOR),
        ),
        col2_min_width=99999,  # Force a linear layout.
    ),
)

CONFIG_SAVE_STYLED = click.style("tutor config save", fg=EXTERNAL_COLOR)
RECON_SAVE_STYLED = click.style("tutor recon save", fg=MAIN_COLOR)

DEFAULT_OVERRIDE_SEQUENCE = json.dumps(
    {
        "$t": "override-sequence",
        "overrides": [
            {
                "$t": "tutor",
                "target": "config.yml",
                "overrides": "$./tutor_config.v.json",
            },
            {
                "$t": "json",
                "target": "env/apps/openedx/config/cms.env.json",
                "overrides": "$./openedx/cms.env.v.json",
            },
            {
                "$t": "json",
                "target": "env/apps/openedx/config/lms.env.json",
                "overrides": "$./openedx/lms.env.v.json",
            },
        ],
    }
)
