# pondsys.cli.menus.support_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

from pondsys.beam.beam import Beam

def supports_menu(beam):
    """
    Submenu for managing supports on the beam.
    """
    while True:
        action = questionary.select(
            "Supports Menu:",
            choices=[
                "Add Support",
                "Remove Support",
                "List Supports",
                "Back to Main Menu",
            ],
            use_shortcuts=True,
        ).ask()

        # Returning to main menu
        if action == "Back to Main Menu":
            break

        # Add a support
        elif action == "Add Support":
            position = questionary.text(
                "Position of support from left end of beam (ft):"
            ).ask()
            spring_constant_TX = questionary.text(
                "Spring constant in x-direction (lb/ft) (Enter 0 if unrestrained):"
            ).ask()
            spring_constant_TY = questionary.text(
                "Spring constant in y-direction (lb/ft) (Enter 0 if unrestrained):"
            ).ask()
            spring_constant_RZ = questionary.text(
                "Rotational spring constant in z-direction (lb-ft/rad) (Enter 0 if unrestrained):"
            ).ask()
            try:
                beam.add_support(
                    float(position),
                    float(spring_constant_TX),
                    float(spring_constant_TY),
                    float(spring_constant_RZ),
                )
                print(f'Added support at {position} ft.')
            except Exception as e:
                print('Error adding support:', e)

        # Remove a support
        elif action == "Remove Support":
            supports = beam.list_supports()
            if not supports:
                logger.info("No supports to remove.")
                continue
            choices = [f"{i+1}: {s}" for i, s in enumerate(supports)]
            choices.append("Cancel")
            selection = questionary.select(
                "Select support to remove:", 
                choices=choices,
                use_shortcuts=True,
            ).ask()
            if selection == "Cancel":
                continue
            else:
                try:
                    index = int(selection.split(":")[0])-1
                except ValueError:
                    logger.error("Invalid selection.")
                    continue
                try:
                    removed = beam.delete_support(index)
                    logger.info(TextStyler.GREEN+f'Removed support {removed}'+TextStyler.RESET)
                except IndexError as e:
                    logger.error(e)

        # List all supports currently in project
        elif action == "List Supports":
            supports = beam.list_supports()
            if not supports:
                logger.info("No supports added.")
            else:
                print("Current Supports:")
                for i, s in enumerate(supports):
                    print(f"{i+1}: {s}")
            questionary.press_any_key_to_continue().ask()
