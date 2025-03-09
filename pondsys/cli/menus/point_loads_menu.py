# pondsys.cli.menus.point_loads_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.cli.menus.load_cases_menu import load_case_choice

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

from pondsys.beam.beam import Beam

def point_loads_menu(beam):
    """
    Submenu for managing point loads on the beam.
    """
    while True:
        action = questionary.select(
            "Point Loads Menu:",
            choices=[
                "Add Point Load",
                "Delete Point Load",
                "List Point Loads",
                "Back to Loading Menu",
            ],
            use_shortcuts=True,
        ).ask()

        # Returning to loading menu
        if action == "Back to Loading Menu":
            break

        # Add point load
        elif action == "Add Point Load":
            position = questionary.text(
                f"Enter position of point load from left end of beam (ft):"
            ).ask()
            magnitude = questionary.text(
                f"Enter magnitude of point load (down is positive) (lb):"
            ).ask()
            load_case = load_case_choice()

            try:
                beam.add_point_load(
                    float(position),
                    float(magnitude),
                    load_case
                )
                logger.info(TextStyler.GREEN+f"Added {load_case} point load of {magnitude} lb at {position} ft."+TextStyler.RESET)
            except Exception as e:
                logger.error('Error adding point load:', e)

        # Delete point load
        elif action == "Delete Point Load":
            point_loads = beam.list_point_loads()
            if not point_loads:
                print("No point loads to delete.")
                continue
            choices = [f"{i+1}: {pl}" for i, pl in enumerate(point_loads)]
            choices.append("Clear All")
            choices.append("Cancel")
            selection = questionary.select(
                "Select point load to delete:",
                choices=choices,
                use_shortcuts=True,
            ).ask()
            if selection == "Cancel":
                continue
            elif selection == "Clear All":
                selected_case = load_case_choice()
                try:
                    beam.clear_point_loads(selected_case)
                    logger.info(TextStyler.GREEN+f"Cleared all point loads for load case {selected_case}."+TextStyler.RESET)
                except Exception as e:
                    logger.error('Error clearing point loads:', e)
            else:
                try:
                    index = int(selection.split(':')[0])-1
                except ValueError:
                    logger.warning("Invalid selection.")
                try:
                    beam.delete_point_load(index)
                    logger.info(TextStyler.GREEN+f"Deleted point load {selection}."+TextStyler.RESET)
                except Exception as e:
                    logger.error('Error deleting point load:', e)

        # List all point loads currently on the beam
        elif action == "List Point Loads":
            point_loads = beam.list_point_loads()
            if not point_loads:
                logger.info("No point loads to list.")
                continue
            else:
                print("Current point loads:")
                for i, pl in enumerate(point_loads):
                    print(f"{i+1}: {pl}")
            questionary.press_any_key_to_continue().ask()
