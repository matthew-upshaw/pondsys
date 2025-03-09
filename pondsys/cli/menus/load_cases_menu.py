# pondsys.cli.menus.load_cases_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.utils.logging_config import logger

load_case_abbr = {
    "Dead Load": "D",
    "Roof Live Load": "Lr",
    "Snow Load": "S",
    "Rain Load": "R",
}

def load_case_choice():
    """
    Menu for selecting a load case.
    """
    while True:
        load_case = questionary.select(
            "Load Case Menu:",
            choices=[
                "Dead Load",
                "Roof Live Load",
                "Snow Load",
                "Rain Load",
                "Cancel"
            ],
            use_shortcuts=True,
        ).ask()

        # Returning to main menu
        if load_case == "Cancel":
            break

        # Return the selected load case
        else:
            return load_case_abbr[load_case]
        