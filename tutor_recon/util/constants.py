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
    show_default=True,
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
