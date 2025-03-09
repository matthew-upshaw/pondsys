# pondsys.cli.menus.loading_menu.py
# Copyright (c) 2025 Matthew Upshaw
# See LICENSE file in project root for full license information.

import questionary

from pondsys.cli.menus.point_loads_menu import point_loads_menu
from pondsys.cli.menus.line_loads_menu import line_loads_menu

from pondsys.utils.styler import TextStyler
from pondsys.utils.logging_config import logger

from pondsys.beam.beam import Beam

def loading_menu(beam):
    """
    Subemenu for managing loading on the beam.
    """
    while True:
        action = questionary.select(
            "Loading Menu:",
            choices=[
                "Impounded Water Depth",
                "Point Loads",
                "Line Loads",
                "Back to Main Menu",
            ],
            use_shortcuts=True,
        ).ask()

        # Returning to main menu
        if action == "Back to Main Menu":
            break

        # Assign impounded water depth
        elif action == "Impounded Water Depth":
            static_head = questionary.text(
                f"Enter static head (in):"
            ).ask()
            hydraulic_head = questionary.text(
                f"Enter hydraulic head (in):"
            ).ask()
            auto_add = questionary.confirm(
                f"Add rain load based on depth and beam slope? (Y/n)"
            ).ask()

            try:
                if (beam.tributary_width > 0):
                    beam.add_or_update_rain_load(
                        (float(static_head), float(hydraulic_head)),
                        bool(auto_add)
                    )
                else:
                    beam.add_or_update_rain_load(
                        (float(static_head), float(hydraulic_head)),
                        auto_add_dist_load = False
                    )
                logger.info(TextStyler.GREEN+f"Assigned static head of {static_head} in and hydraulic head of {hydraulic_head} in."+TextStyler.RESET)
                if bool(auto_add) & (beam.tributary_width > 0):
                    logger.info(TextStyler.GREEN+f"Automatically added rain load."+TextStyler.RESET)
                elif bool(auto_add) & (beam.tributary_width == 0):
                    logger.warning("Tributary width must be greater than 0 to automatically add rain load.")
            except Exception as e:
                logger.error(f"Error assigning impounded water depth: {e}")

        # Point Loads Menu
        elif action == "Point Loads":
            point_loads_menu(beam)

        # Line Loads Menu
        elif action == "Line Loads":
            line_loads_menu(beam)
            