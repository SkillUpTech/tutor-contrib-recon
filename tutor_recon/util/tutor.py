"""Re-exports of Tutor commands and tutor-related utility functions are added to this file as needed."""

import cloup
import tutor.commands.config
from .constants import CONFIG_SAVE_STYLED
from .cli import emit

tutor_config_save = tutor.commands.config.save


def run_tutor_config_save(context: cloup.Context) -> None:
    emit(f"Running {CONFIG_SAVE_STYLED}.")
    context.invoke(tutor_config_save)
