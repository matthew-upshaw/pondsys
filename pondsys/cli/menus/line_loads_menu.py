# pondsys.cli.menus.line_loads_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.cli.menus.load_cases_menu import load_case_choice

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

from pondsys.beam.beam import Beam

def line_loads_menu(beam):
    """
    Submenu for managing line loads on the beam.
    """
    while True:
        action = questionary.select(
            "Line Loads Menu:",
            choices=[
                "Add Line Load",
                "Delete Line Load",
                "List Line Loads",
                "Back to Loading Menu",
            ],
            use_shortcuts=True,
        ).ask()

        # Returning to loading menu
        if action == "Back to Loading Menu":
            break

        # Add line load
        elif action == "Add Line Load":
            start_position = questionary.text(
                f"Enter starting position of line load from left end of beam (ft):"
            ).ask()
            stop_position = questionary.text(
                f"Enter ending position of line load from left end of beam (ft):"
            ).ask()
            start_magnitude = questionary.text(
                f"Enter starting magnitude of line load (down is positive) (lb/ft):"
            ).ask()
            stop_magnitude = questionary.text(
                f"Enter ending magnitude of line load (down is positive) (lb/ft):"
            ).ask()
            load_case = load_case_choice()

            try:
                beam.add_dist_load(
                    float(start_position),
                    float(stop_position),
                    float(start_magnitude),
                    float(stop_magnitude),
                    load_case
                )
                logger.info(TextStyler.GREEN+f"Added {load_case} line load of ({start_magnitude}, {stop_magnitude}) lb/ft at ({start_position}, {stop_position}) ft."+TextStyler.RESET)
            except Exception as e:
                logger.error('Error adding point load:', e)

        # Delete line load
        elif action == "Delete Line Load":
            line_loads = beam.list_dist_loads()
            if not line_loads:
                logger.info("No line loads to delete.")
                continue
            choices = [f"{i+1}: {ll}" for i, ll in enumerate(line_loads)]
            choices.append("Clear All")
            choices.append("Cancel")
            selection = questionary.select(
                "Select line load to delete:",
                choices=choices,
                use_shortcuts=True,
            ).ask()
            if selection == "Cancel":
                continue
            elif selection == "Clear All":
                selected_case = load_case_choice()
                try:
                    beam.clear_dist_loads(selected_case)
                    logger.info(TextStyler.GREEN+f"Cleared all point loads for load case {selected_case}."+TextStyler.RESET)
                except Exception as e:
                    logger.error('Error clearing point loads:', e)
            else:
                try:
                    index = int(selection.split(':')[0])-1
                except ValueError:
                    logger.info("Invalid selection.")
                try:
                    beam.delete_dist_load(index)
                    logger.info(TextStyler.GREEN+f"Deleted point load {selection}."+TextStyler.RESET)
                except Exception as e:
                    logger.error('Error deleting point load:', e)

        # List all point loads currently on the beam
        elif action == "List Line Loads":
            line_loads = beam.list_dist_loads()
            if not line_loads:
                logger.info("No line loads to list.")
                continue
            else:
                print("Current line loads:")
                for i, ll in enumerate(line_loads):
                    print(f"{i+1}: {ll}")
            questionary.press_any_key_to_continue().ask()
